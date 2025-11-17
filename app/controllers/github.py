import urllib.parse
from app.config import settings
import httpx as httpx
import app.helpers.github_helper as github_helper
import app.utils.mongo_utils as mongo_utils
from app.utils.jwt_utils import create_jwt_token

async def github_auth():
    try:
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
            "scope": "user:email read:user repo",
        }

        auth_url = (
            "https://github.com/login/oauth/authorize?"
            + urllib.parse.urlencode(params)
        )

        return auth_url
    except Exception as e:
        raise e


async def github_callback(code: str):
    try:
        data = await github_helper.authenticate_github_user(code)
        user_record = await mongo_utils.insert_github_user(data)

        # Ensure Mongo ObjectId is serialized
        if "_id" in user_record:
            user_record["_id"] = str(user_record["_id"])

        token_payload = {
            "user_id": user_record.get("user_id"),
            "github_id": user_record.get("github_id"),
            "github_access_token": user_record.get("github_access_token"),
        }
        jwt_token = create_jwt_token(token_payload)

        return {
            "user": user_record,
            "token": jwt_token,
            "token_type": "bearer",
            "expires_in_days": settings.JWT_EXPIRY_DAYS,
        }
    except Exception as e:
        raise e

async def get_all_repos(access_token: str):
    try:
        data = await github_helper.get_all_repos(access_token)
        return data
    except Exception as e:
        raise e

async def clone_repo(repo_name: str, access_token: str):
    try:
        data = await github_helper.clone_github_repo(repo_name, access_token)
        return data
    except Exception as e:
        raise e

async def get_repo_by_id(repo_id: str, access_token: str):
    try:
        data = await github_helper.get_repo_by_id(repo_id, access_token)
        return data
    except Exception as e:
        raise e