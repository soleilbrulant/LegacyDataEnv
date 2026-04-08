from envs.legacy_data.env import app

# This simply exports your existing app so the validator finds it where it expects.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)