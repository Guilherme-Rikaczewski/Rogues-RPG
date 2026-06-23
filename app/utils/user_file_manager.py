import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader


load_dotenv()

CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
CLOUDINARY_NAME = os.getenv("CLOUDINARY_NAME")

config = cloudinary.config(
    secure=True,
    cloud_name=CLOUDINARY_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)


def upload_image(
    file, user_id, img_id, extra_folder='', max_width=2048, max_height=2048
) -> dict:
    result = cloudinary.uploader.upload(
        file,
        folder=f'users/user_{user_id}{extra_folder}',
        public_id=img_id,
        transformation=[
            {"quality": "auto"},
            {"fetch_format": "auto"},
            {"width": max_width, "height": max_height, "crop": "limit"},
            {"strip_metadata": True}
        ]
    )
    url = result["secure_url"]
    size = result["bytes"]
    public_id = result["public_id"]
    return {
        'url': url,
        'size': size,
        'public_id': public_id
    }


def delete_image(public_id):
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass
