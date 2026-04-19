"""
epiguard-ai — Main training entry point.
Run via:  python -m training.train
Or:       docker-compose --profile train run --rm model-trainer
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("═══ epiguard-ai training started ═══")

    # Import here so settings are loaded first
    from training.scripts.build_dataset import build_dataset
    from training.scripts.train_model   import train_and_save
    from training.evaluation.evaluate   import evaluate_and_report

    logger.info("Step 1/3 — Building dataset")
    X_train, X_test, y_train, y_test = build_dataset()

    logger.info("Step 2/3 — Training model")
    model = train_and_save(X_train, y_train)

    logger.info("Step 3/3 — Evaluating model")
    evaluate_and_report(model, X_test, y_test)

    logger.info("═══ Training complete — epiguard-ai.pkl saved ═══")


if __name__ == "__main__":
    main()
