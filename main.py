from fastapi import FastAPI
import logging

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/app_health")
def health_check():

    logger.info("Health check requested")

    result = {"status": "healthy"}

    logger.info("Health check completed successfully")

    return result