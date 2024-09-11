from pathlib import Path
from bs4 import BeautifulSoup
import msgspec
import lxml
from typing import List
import re
from openai import OpenAI
import time

OPENAI_AI_KEY = ""
CLIENT = OpenAI(api_key=OPENAI_AI_KEY)

class WebPage(msgspec.Struct, gc=False):
	url: str
	content: str
	encoding: str
	title: str = ""
	context: str = ""
	soup: BeautifulSoup = None

	def __post_init__(self):
		self.soup = BeautifulSoup(self.content, "lxml")
		title = self.soup("title")
		self.title = title[-1].text.strip() if title else self.url
	
	def get_text(self) -> List[str]:
		[s.decompose() for s in self.soup(['style', 'script', 'code', '[document]', 'head'])]
		return [re.sub(r'\s+',' ', string) for string in self.soup.stripped_strings if string]
	
	def get_summary(self):
		body = self.soup.find("body")
		if not body:
			return ""
		yield "AI Summary: "
		body_strings = [re.sub(r'\s+',' ', string).strip() for string in body.stripped_strings]
		body_strings = [list(re.findall(r'\b[a-zA-Z0-9]+\b', string)) for string in body_strings]
		body_strings = [" ".join(string) for string in body_strings]
		body_strings = [s for s in body_strings if len(s) >= 5]
		response = CLIENT.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[
				{"role": "system", "content": "Summarize following webpage content using 30 completion_tokens or less. Not complete sentence, don't mention the word summary"},
				{"role": "user", "content": "\n".join(body_strings)}
			],
			max_tokens=100,
			stream=True
		)
		for chunk in response:
			if chunk.choices[0].delta.content is not None:
				yield chunk.choices[0].delta.content
	
	def get_context(self, tokens=None) -> str:
		tokens = " ".join(tokens).split(" ")
		if tokens and (body := self.soup.find("body")):
			body_strings = [re.sub(r'\s+',' ', string).strip() for string in body.stripped_strings]
			body_strings = " ".join(body_strings)
			body_strings = " ".join(re.findall(r'\b[a-zA-Z0-9]+\b', body_strings))
			for token in tokens:
				pos = body_strings.lower().find(token)
				if pos > -1:
					self.context = body_strings[pos:pos+300]
		return self.context
	
	@classmethod
	def from_path(cls, path: Path):
		with open(path, "r", encoding="utf-8") as f:
			return decoder.decode(f.read())

decoder = msgspec.json.Decoder(type=WebPage)

if __name__ == "__main__":
	webpage = WebPage.from_path(Path("DEV\\ngs_ics_uci_edu\\f46429fcd2d984473eac85f30165384427dbd4471e7750f7989fc79b2a70ddb2.json"))
	print(webpage.url)
	print(webpage.title)
	print(webpage.get_text())
