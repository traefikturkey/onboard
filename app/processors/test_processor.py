class TestProcessor:
    def process(self, articles):
        for a in articles:
            a.processed = "test_processor"
        return articles
