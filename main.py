from fastapi import FastAPI
from http import HTTPStatus

import logging

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI()

UserS={"user": "Ram","email":"rampathuri536@gmail.com","phone":"+91 949 494 9494","address":"Hyderabad, Telangana, India","status":"active","user_name":"ram","user_id":1050,"created_at":"2023-01-01T00:00:00Z","Last_updated_at":"2023-01-01T00:00:00Z"}


@app.get("/app_health")
def health_check():

    logger.info("Health check requested")

    result = {"status": "healthy"}

    logger.info("Health check completed successfully", extra={"status_code": HTTPStatus.OK})

    return result

# TODO: Implement the fake json with actual to db to get user's data.

@app.get("/Get1_user/{user_id}")
def get_user_by_id(user_id: int):

    logger.info(f"User requested with ID: {user_id}")

    if UserS['user_id'] == user_id:
        logger.info(f"User with ID {user_id} found", extra={"status_code": HTTPStatus.OK})
        return UserS
    else:
        logger.warning(f"User with ID {user_id} not found", extra={"status_code": HTTPStatus.NOT_FOUND})
        return {"error": "User not found"}, HTTPStatus.NOT_FOUND


@app.get("/Get_user/me")
def get_current_user():

    logger.info("Current user requested",extra={"status_code": HTTPStatus.BAD_REQUEST})

    return {"user": "Ram","email":"rampathuri536@gmail.com","phone":"+91 949 494 9494","address":"Hyderabad, Telangana, India","status":"active","user_name":"ram","user_id":1,"created_at":"2023-01-01T00:00:00Z","Last_updated_at":"2023-01-01T00:00:00Z"}


