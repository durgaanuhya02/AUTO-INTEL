#!/usr/bin/env python3
"""
Model Training Script - Pre-trains all ML models for production use
Run this script to train models before starting the system
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.ml_training_service import MLTrainingService
from backend.services.real_data_processor import RealDataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main training function"""
    try:
        logger.info("🤖 Starting ML Model Training...")

        # Initialize data processor
        data_processor = RealDataProcessor()
        await data_processor.initialize()

        # Initialize training service
        training_service = MLTrainingService()
        await training_service.initialize()

        # Train all models
        results = await training_service.train_all_models(data_processor)

        # Report results
        logger.info("📊 Training Results:")
        for model_name, result in results.items():
            if result.get("status") == "success":
                logger.info(f"✅ {model_name}: {result}")
            else:
                logger.error(f"❌ {model_name}: {result}")

        # Check model availability
        model_status = await training_service._load_existing_models()
        logger.info(f"📁 Models saved to: {training_service.models_dir}")

        logger.info("🎉 ML Model Training Complete!")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())