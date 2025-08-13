import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from app.models.feed_article import FeedArticle
from app.processors.title_editor import TitleEditor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestTitleEditor(unittest.TestCase):
    def setUp(self):
        # Create a mock parent object that FeedArticle expects
        self.mock_parent = MagicMock()
        self.mock_parent.id = "test_parent_id"

    def test_hostname_resolves_success(self):
        editor = TitleEditor()
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            self.assertEqual(editor.hostname_resolves("localhost"), 1)

    def test_hostname_resolves_failure(self):
        editor = TitleEditor()
        with patch("socket.gethostbyname", side_effect=OSError):
            self.assertEqual(editor.hostname_resolves("badhost"), 0)

    @patch.dict(os.environ, {"OLLAMA_URL": "localhost"})
    @patch("app.processors.title_editor.TitleEditor.hostname_resolves", return_value=1)
    @patch("app.processors.title_editor.Ollama")
    @patch("app.processors.title_editor.StructuredOutputParser")
    @patch("app.processors.title_editor.ResponseSchema")
    @patch("app.processors.title_editor.PromptTemplate")
    @patch("app.processors.title_editor.SystemMessage")
    @patch("app.processors.title_editor.HumanMessagePromptTemplate")
    @patch("app.processors.title_editor.ChatPromptTemplate")
    @patch("app.processors.title_editor.calculate_sha1_hash", return_value="hash")
    def test_init_with_ollama_url(
        self,
        mock_hash,
        mock_chat_prompt,
        mock_human_prompt,
        mock_system_msg,
        mock_prompt_template,
        mock_response_schema,
        mock_structured_parser,
        mock_ollama,
        mock_hostname_resolves,
    ):
        editor = TitleEditor()
        self.assertTrue(hasattr(editor, "llama3_chain"))
        self.assertTrue(hasattr(editor, "mistral_chain"))
        self.assertEqual(editor.script_hash, "hash")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_ollama_url(self):
        editor = TitleEditor()
        self.assertFalse(hasattr(editor, "llama3_chain"))
        self.assertFalse(hasattr(editor, "mistral_chain"))

    @patch.dict(os.environ, {"OLLAMA_URL": "localhost"})
    @patch("app.processors.title_editor.TitleEditor.hostname_resolves", return_value=1)
    @patch("app.processors.title_editor.Ollama")
    @patch("app.processors.title_editor.StructuredOutputParser")
    @patch("app.processors.title_editor.ResponseSchema")
    @patch("app.processors.title_editor.PromptTemplate")
    @patch("app.processors.title_editor.SystemMessage")
    @patch("app.processors.title_editor.HumanMessagePromptTemplate")
    @patch("app.processors.title_editor.ChatPromptTemplate")
    @patch("app.processors.title_editor.calculate_sha1_hash", return_value="hash")
    def test_process_articles(
        self,
        mock_hash,
        mock_chat_prompt,
        mock_human_prompt,
        mock_system_msg,
        mock_prompt_template,
        mock_response_schema,
        mock_structured_parser,
        mock_ollama,
        mock_hostname_resolves,
    ):
        editor = TitleEditor()
        # Mock chains
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"title": "Edited Title"}
        editor.llama3_chain = mock_chain
        editor.mistral_chain = mock_chain
        # Create articles
        article1 = FeedArticle(
            original_title="Original Title",
            title="",
            link="https://example.com",
            description="Description",
            pub_date=None,
            processed="not_hash",
            parent=self.mock_parent,
        )
        articles = [article1]
        result = editor.process(articles)
        self.assertEqual(result[0].title, "Edited Title")
        self.assertEqual(result[0].processed, "hash")

    @patch.dict(os.environ, {"OLLAMA_URL": "localhost"})
    @patch("app.processors.title_editor.TitleEditor.hostname_resolves", return_value=0)
    def test_process_no_hostname(self, mock_hostname_resolves):
        editor = TitleEditor()
        article1 = FeedArticle(
            original_title="Original Title",
            title="",
            link="https://example.com",
            description="Description",
            pub_date=None,
            processed="not_hash",
            parent=self.mock_parent,
        )
        articles = [article1]
        result = editor.process(articles)
        self.assertEqual(result, articles)

    @patch.dict(os.environ, {"OLLAMA_URL": "localhost"})
    @patch("app.processors.title_editor.TitleEditor.hostname_resolves", return_value=1)
    @patch("app.processors.title_editor.Ollama")
    @patch("app.processors.title_editor.StructuredOutputParser")
    @patch("app.processors.title_editor.ResponseSchema")
    @patch("app.processors.title_editor.PromptTemplate")
    @patch("app.processors.title_editor.SystemMessage")
    @patch("app.processors.title_editor.HumanMessagePromptTemplate")
    @patch("app.processors.title_editor.ChatPromptTemplate")
    @patch("app.processors.title_editor.calculate_sha1_hash", return_value="hash")
    def test_process_articles_with_error(
        self,
        mock_hash,
        mock_chat_prompt,
        mock_human_prompt,
        mock_system_msg,
        mock_prompt_template,
        mock_response_schema,
        mock_structured_parser,
        mock_ollama,
        mock_hostname_resolves,
    ):
        """Test that process method handles chain errors gracefully"""
        editor = TitleEditor()
        # Mock chains that raise exceptions
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("Chain error")
        editor.llama3_chain = mock_chain
        editor.mistral_chain = mock_chain

        article1 = FeedArticle(
            original_title="Original Title",
            title="",
            link="https://example.com",
            description="Description",
            pub_date=None,
            processed="not_hash",
            parent=self.mock_parent,
        )
        articles = [article1]
        result = editor.process(articles)
        # Article should remain unchanged when both chains fail
        self.assertEqual(
            result[0].title, "Original Title"
        )  # Title stays as original when processing fails
        self.assertEqual(result[0].processed, "not_hash")

    @patch.dict(os.environ, {"OLLAMA_URL": "localhost"})
    @patch("app.processors.title_editor.TitleEditor.hostname_resolves", return_value=1)
    @patch("app.processors.title_editor.Ollama")
    @patch("app.processors.title_editor.StructuredOutputParser")
    @patch("app.processors.title_editor.ResponseSchema")
    @patch("app.processors.title_editor.PromptTemplate")
    @patch("app.processors.title_editor.SystemMessage")
    @patch("app.processors.title_editor.HumanMessagePromptTemplate")
    @patch("app.processors.title_editor.ChatPromptTemplate")
    @patch("app.processors.title_editor.calculate_sha1_hash", return_value="hash")
    def test_process_articles_already_processed(
        self,
        mock_hash,
        mock_chat_prompt,
        mock_human_prompt,
        mock_system_msg,
        mock_prompt_template,
        mock_response_schema,
        mock_structured_parser,
        mock_ollama,
        mock_hostname_resolves,
    ):
        """Test that already processed articles are skipped"""
        editor = TitleEditor()

        article1 = FeedArticle(
            original_title="Original Title",
            title="Already Processed",
            link="https://example.com",
            description="Description",
            pub_date=None,
            processed="hash",  # Same as script_hash
            parent=self.mock_parent,
        )
        articles = [article1]
        result = editor.process(articles)
        # Article should remain unchanged since it's already processed
        self.assertEqual(result[0].title, "Already Processed")
        self.assertEqual(result[0].processed, "hash")


if __name__ == "__main__":
    unittest.main()
