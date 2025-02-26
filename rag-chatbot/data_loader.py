import glob
import os


def load_data_from_chunks(directory, logger):
    """Loads all chunked files from a directory into a single list of logs."""
    data = []
    for file in sorted(glob.glob(os.path.join(directory, 'chunk_*.txt'))):
        with open(file, 'r', encoding='latin-1') as f:
            file_data = f.read().splitlines()
            logger.info(f"Loaded {len(file_data)} lines from {file}")
            data.extend(file_data)
    logger.info(f"Total lines loaded from chunks: {len(data)}")
    return data


def filter_data(data, exclusion_keywords=None, limit_per_keyword=None, logger=None):
    if exclusion_keywords is None:
        exclusion_keywords = []
    if limit_per_keyword is None:
        limit_per_keyword = {}

    filtered_data = []
    keyword_counts = {keyword: 0 for keyword in exclusion_keywords}

    for log in data:
        if any(keyword in log for keyword in exclusion_keywords):
            for keyword in exclusion_keywords:
                if keyword in log:
                    if keyword_counts[keyword] < limit_per_keyword.get(keyword, float('inf')):
                        filtered_data.append(log)
                        keyword_counts[keyword] += 1
                        logger.info(f"Included log containing '{
                                    keyword}': {log[:100]}...")
                    else:
                        logger.info(f"Excluded log containing '{
                                    keyword}' due to limit: {log[:100]}...")
                    break
        else:
            filtered_data.append(log)

    logger.info(f"Total logs after filtering: {len(filtered_data)}")
    for keyword, count in keyword_counts.items():
        logger.info(f"Total logs containing '{keyword}': {count}")

    return filtered_data
