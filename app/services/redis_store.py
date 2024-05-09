import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RedisStore:
  def __init__(self):
    import redis
    self.redis = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'))
    self.namespace = os.getenv('REDIS_NAMESPACE', f'onboard/{os.environ.get("FLASK_ENV", "development")}/favicons')

  def processed_domain_count(self):
    try:
      return self.redis.scard(f"{self.namespace}:processed_domains")
    except Exception as ex:
      logger.error(f"Error in get_processed_domain_count_from_db(): {ex}")
      return 0

  def save_processed_domain(self, normalized_domain, reason='completed'):
    try:
      self.redis.sadd(f"{self.namespace}:processed_domains", normalized_domain)
      logger.info(f"Domain {normalized_domain} processed with reason {reason}")
    except Exception as ex:
      logger.error(f"Error in save_processed_domain({normalized_domain}): {ex}")

  def is_domain_processed(self, normalized_domain):
    try:
      return self.redis.sismember(f"{self.namespace}:processed_domains", normalized_domain)
    except Exception as ex:
      logger.error(f"Error checking is_domain_processed({normalized_domain}): {ex}")
      return False
