import tiktoken, os, anthropic, sys
from openai import OpenAI
import google.generativeai as genai

class a11y_llm():
    def __init__(self, modelName):
        self.modelName = modelName

    def token_length(self, data):
        enc = tiktoken.encoding_for_model(self.modelName)
        return len(enc.encode(data))

class openai_gpt(a11y_llm):
    def __init__(self, modelName):
        super().__init__(modelName)
        self.model = OpenAI(
            organization=os.environ['OPENAI_ORG_ID'],
            api_key=os.environ['OPENAI_API_KEY']
        )
        self.chatHistory = []
    
    def send_message(self, message):
        self.chatHistory.append({"role": "user", "content": message})
        print(f"Input tokens: {self.token_length(str(self.chatHistory))}")
        completion = self.model.chat.completions.create(
            model=self.modelName,
            messages=self.chatHistory)
        response = completion.choices[0].message.content
        print(f"Output tokens: {self.token_length(response)}")
        self.chatHistory.append({"role": "assistant", "content": response})
        self.openai_api_cost(completion.usage, self.modelName)
        return response
    
    def single_query(self, message):
        completion = self.model.chat.completions.create(
            model=self.modelName,
            messages=[{"role": "user", "content": message}])
        return completion.choices[0].message.content
    
    def single_query_system(self, message, systemPrompt):
        completion = self.model.chat.completions.create(
            model=self.modelName,
            messages=[{"role": "system", "content":message},
                      {"role": "user", "content":systemPrompt}])
        return completion.choices[0].message.content
    
    def openai_api_cost(self, usage, model):
        pricing = {
            'gpt-3.5-turbo-0125': {
                'prompt': 0.5,
                'completion': 1.5,
            },
            'gpt-4-turbo-preview': {
                'prompt': 10,
                'completion': 30,
            },
        }

        try:
            model_pricing = pricing[model]
        except KeyError:
            raise ValueError("Invalid model specified")

        million = 1000000
        prompt_cost = usage.prompt_tokens * ( model_pricing['prompt'] / million )
        completion_cost = usage.completion_tokens * ( model_pricing['completion'] / million )

        total_cost = prompt_cost + completion_cost
        # round to 6 decimals
        total_cost = round(total_cost, 6)

        print(f"\nTokens used:  {usage.prompt_tokens:,} prompt + {usage.completion_tokens:,} completion = {usage.total_tokens:,} tokens")
        print(f"Cost {model}: ${total_cost:.4f}\n")

class google_gemini(a11y_llm):
    def __init__(self, modelName):
        super().__init__(modelName)
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        self.model = genai.GenerativeModel(modelName)
        self.chat = None
    
    def send_message(self, message):
        response = self.chat.send_message(message)
        return response.text
    
    def token_length(self, data):
        return self.model.count_tokens(data)


class anthropic_claude(a11y_llm):
    def __init__(self, modelName):
        super().__init__(modelName)
        self.model = anthropic.Anthropic(
            api_key=os.environ['ANTHROPIC_API_KEY']
        )
        self.chatHistory = []
        self.systemPrompt = None

    def send_message(self, message):
        self.chatHistory.append({"role": "user", "content": message})
        completion = self.model.messages.create(
            max_tokens=2028,
            model=self.modelName,
            system=self.systemPrompt,
            messages=self.chatHistory)
        print(f"Input tokens: {completion.usage.input_tokens}")
        print(f"Output tokens: {completion.usage.output_tokens}")
        response = completion.content[0].text
        self.chatHistory.append({"role": "assistant", "content": response})
        return response
    
    def token_length(data):
        tokenzier = anthropic._tokenizers.sync_get_tokenizer()
        enc_data = tokenzier.encode(str(data))
        return len(enc_data)

if __name__ == "__main__":
    llm = openai_gpt('gpt-3.5-turbo-0125')
    print(llm.send_message("Hello, how are you?"))