"""End-to-end test: dataset screenshots -> OCR -> emotion prediction -> DB metrics/stage.

This script is intended for manual/student testing.

Pipeline:
  Kaggle dataset download
  image(s) -> OCR chat parsing (sender, text)
  ConversationService.process_chat() persists:
    - Message rows with emotion + score
    - DailyRelationshipMetrics
    - RelationshipStage
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import kagglehub
from sqlalchemy.orm import Session

# Ensure `backend/` is on PYTHONPATH so `import app...` works
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal, init_db
from app.db.models import Conversation, Message, RelationshipStage, User
from app.services.conversation_service import ConversationService
from app.services.ocr_service import extract_chat_text


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _is_image_file(p: Path) -> bool:
    return p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file()


def _get_or_create_user(db: Session, name: str) -> User:
    normalized = (name or "").strip() or "Unknown"
    user = db.query(User).filter(User.name == normalized).one_or_none()
    if user is None:
        user = User(name=normalized)
        db.add(user)
        db.flush()
    return user


def _get_or_create_conversation(db: Session, sender_a: str, sender_b: str) -> Conversation:
    user_a = _get_or_create_user(db, sender_a)
    user_b = _get_or_create_user(db, sender_b)

    conversation = (
        db.query(Conversation)
        .filter(Conversation.person_a_id == user_a.id, Conversation.person_b_id == user_b.id)
        .one_or_none()
    )
    if conversation is None:
        conversation = Conversation(person_a_id=user_a.id, person_b_id=user_b.id)
        db.add(conversation)
        db.flush()
    return conversation


def _pick_two_senders(messages: List[Dict[str, Any]]) -> Tuple[str, str]:
    senders: List[str] = []
    for m in messages:
        sender = str(m.get("sender", "")).strip()
        if sender and sender not in senders:
            senders.append(sender)
        if len(senders) >= 2:
            break

    sender_a = senders[0] if senders else "Unknown"
    sender_b = senders[1] if len(senders) > 1 else sender_a
    return sender_a, sender_b


def _parse_human_chat_txt(chat_path: Path, *, max_messages: int) -> List[Dict[str, Any]]:
    """
    Fallback parser for datasets that contain conversation text instead of screenshots.

    Expected line format:
      Human 1: Hi!
      Human 2: What is your favorite holiday?
    """
    messages: List[Dict[str, Any]] = []
    with chat_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            sender, text = line.split(":", 1)
            sender = sender.strip()
            text = text.strip()
            if sender and text:
                messages.append({"sender": sender, "text": text})
            if len(messages) >= max_messages:
                break
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3, help="Max number of images to process")
    parser.add_argument("--start", type=int, default=0, help="Start index in the image list")
    parser.add_argument("--dataset", type=str, default="projjal1/human-conversation-training-data")
    parser.add_argument("--max-messages", type=int, default=50, help="Max messages when falling back to text parsing")
    parser.add_argument("--local-images-dir", type=str, default="", help="Optional local folder containing screenshot images")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    dataset_path: Path
    if args.local_images_dir:
        dataset_path = Path(args.local_images_dir).expanduser().resolve()
        if not dataset_path.exists() or not dataset_path.is_dir():
            raise RuntimeError(f"--local-images-dir does not exist or is not a directory: {dataset_path}")
        if args.verbose:
            print(f"[INFO] Using local images dir: {dataset_path}")
    else:
        dataset_path_str: str = kagglehub.dataset_download(args.dataset)
        dataset_path = Path(dataset_path_str)
    if args.verbose:
        print(f"[INFO] Dataset downloaded to: {dataset_path}")

    # Collect images from the dataset folder (if any).
    image_paths = [p for p in dataset_path.rglob("*") if _is_image_file(p)]
    image_paths.sort()
    chosen = image_paths[args.start : args.start + args.limit]

    init_db()
    db = SessionLocal()

    try:
        if chosen:
            print(
                f"[INFO] Found {len(image_paths)} images. Processing {len(chosen)} starting at index {args.start}."
            )
            for idx, img_path in enumerate(chosen, start=args.start):
                print(f"\n[TEST] ({idx+1}/{args.start+len(chosen)}) OCR image: {img_path}")

                messages = extract_chat_text(str(img_path))
                print(f"[INFO] OCR extracted {len(messages)} messages")
                if not messages:
                    continue

                sender_a, sender_b = _pick_two_senders(messages)
                conversation = _get_or_create_conversation(db, sender_a=sender_a, sender_b=sender_b)

                messages_payload: List[Dict[str, Any]] = [
                    {"sender": m.get("sender", ""), "text": m.get("text", ""), "timestamp": m.get("timestamp")}
                    for m in messages
                ]

                result = ConversationService(db).process_chat(
                    conversation_id=conversation.id,
                    messages=messages_payload,
                )
                stage = result.get("relationship_stage", "stranger")

                print(f"[OK] conversation_id={conversation.id}, relationship_stage={stage}")
                if args.verbose:
                    print(f"[DEBUG] emotions_detected={result.get('emotions_detected')}")
        else:
            # Fallback: datasets can ship plain text chats only.
            chat_txt = dataset_path / "human_chat.txt"
            if not chat_txt.exists():
                raise RuntimeError(f"No images found and missing {chat_txt}")

            print(f"[WARN] No images found. Falling back to text parsing: {chat_txt}")
            messages = _parse_human_chat_txt(chat_txt, max_messages=args.max_messages)
            print(f"[INFO] Parsed {len(messages)} messages from text file")
            if not messages:
                raise RuntimeError(f"Text parsing produced 0 messages from {chat_txt}")

            sender_a, sender_b = _pick_two_senders(messages)
            conversation = _get_or_create_conversation(db, sender_a=sender_a, sender_b=sender_b)
            result = ConversationService(db).process_chat(conversation_id=conversation.id, messages=messages)
            stage = result.get("relationship_stage", "stranger")
            print(f"[OK] conversation_id={conversation.id}, relationship_stage={stage}")
            if args.verbose:
                print(f"[DEBUG] emotions_detected={result.get('emotions_detected')}")
    finally:
        db.close()

    print(f"\n[DONE] Completed OCR+emotion+relationship test at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()

