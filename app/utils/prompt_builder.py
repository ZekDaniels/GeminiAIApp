import logging

logger = logging.getLogger("app")


class PromptBuilder:
    @staticmethod
    def construct_prompt(history, user_query, pdf_content, only_text):
        """Construct a prompt for the Generative AI model."""
        history_prompt = "\n".join(
            [f"User: {h.user_query}\nAssistant: {h.assistant_response}" for h in history]
        )
        if only_text:
            return f"{history_prompt}\nUser: {user_query}\n\nAssistant:"
        return f"{history_prompt}\nUser: {user_query}\n\nPDF Content:\n{pdf_content}\nAssistant:"
