from queue import Queue
from pathlib import Path
from typing import Set
from threading import Lock
import platform
import os

OS_WINDOWS = platform.system() == "Windows"		# Flag for if OS is Windows.

class Frontier:
	def __init__(self, source: Path, restart: bool):
		self.is_running = True
		self.to_be_read = Queue()
		self.crawled: Set[str] = set()                  # Set of crawled files to keep track of which files don't need to be crawled again.
		self.document_count: int = 0					# The total number of valid documents.
		self.source: Path = source                      # Directory path containg webpages to index.
		self.crawled_save_path = Path("crawled.txt")    # File path for names of crawled files.
		self.crawled_file = None
		self.index_of_crawled_file = None
		self.crawled_file_lock = Lock()
		self.file_position = 0
		self.current_id = 0

		# If the restart flag was not selected and the save files exist, then load them into memory.
		if not restart and self.crawled_save_path.exists():
			self.read_save_files()
		# If the restart flag was selected or the save files don't exist, create them with empty contents.
		else:
			for file in os.listdir("partial"):
				os.remove(f"partial/{file}")
			self.index_count = 0
			with open(self.crawled_save_path, "w"), open(f"index_of_{self.crawled_save_path}", "w"):
				print("Starting from empty set.")

		self.crawled_file = open(self.crawled_save_path, "a")
		self.index_of_crawled_file = open(f"index_of_{self.crawled_save_path}", "a")
		for file in self.source.rglob("*.json"):
			if str(file) in self.crawled:
				continue
			self.to_be_read.put(file)
	 
	def read_crawled_file(self) -> None:
		""" Read and load crawled save file into memory. """
		with open(self.crawled_save_path, "r") as file:
			for file_path in file:
				self.crawled.add(file_path.strip())
		self.file_position = os.path.getsize(self.crawled_save_path)
		self.current_id = len(self.crawled)
			
	def read_save_files(self) -> None:
		""" Reads and loads save files into memory. """
		self.read_crawled_file()
		print(f"Loaded {len(self.crawled)} pages.")

	def update_crawled_list(self, file_path: Path, id: int) -> None:
		self.crawled.add(file_path.name)
		# Write the file path of this page to the crawled save file.
		line = f"{file_path}\n"
		self.crawled_file.write(line)

		# Each line of the index of crawled is of the form: 
		# 	<id>,<file_position>
		# ex.
		#	3,8753
		#   27,16536
		# The file path of document id 3 can be found at byte 8753 in the crawled save file.
		# The file path of document id 27 can be found at byte 16536.
		self.index_of_crawled_file.write(f"{id},{self.file_position}\n")
		self.file_position += len(line) + OS_WINDOWS

	def get_tbr_file_path(self):
		try:
			file_path = self.to_be_read.get(block=False)
			id = self.current_id
			self.current_id += 1
			return (file_path, id)
		except:
			return (None, None)