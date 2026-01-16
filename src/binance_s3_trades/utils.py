import os


def local_path_for_key(key: str, prefix: str, target_dir: str) -> str:
    """
    Compute and return the local file path for an S3 key.
    """
    return os.path.join(target_dir, key[len(prefix) :] if key.startswith(prefix) else key)
