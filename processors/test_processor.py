class TestProcessor:
  """A tiny processor used by tests that marks articles as processed."""

  def process(self, articles):
    for a in articles:
      # mark as processed to simulate transformation
      a.processed = "test_processor"
    return articles
