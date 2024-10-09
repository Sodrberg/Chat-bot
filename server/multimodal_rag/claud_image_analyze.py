import os
import base64
import anthropic
import json
import time
from dotenv import load_dotenv

class ClaudeImageAnalyzer:
    def __init__(self, image_directory, output_file_path):
        load_dotenv()
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.image_directory = image_directory
        self.output_file_path = output_file_path
        self.max_images_per_request = 10
        self.image_batches = self._split_image_batches()
        self.total_requests = len(self.image_batches)
        self._initialize_output_file()

    def _split_image_batches(self):
        image_files = os.listdir(self.image_directory)
        return [image_files[i:i + self.max_images_per_request] for i in range(0, len(image_files), self.max_images_per_request)]

    def _initialize_output_file(self):
        os.makedirs(os.path.dirname(self.output_file_path), exist_ok=True)
        with open(self.output_file_path, "w") as file:
            file.write("[")

    def image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
            media_type = "image/png"  # Modify based on your image type
            return media_type, base64_data

    def analyze_images(self):
        print(f"Total number of requests to be made: {self.total_requests}")
        for batch_index, image_batch in enumerate(self.image_batches):
            start_time = time.time()
            messages = self._prepare_messages(image_batch)
            response = self._send_request(messages)
            elapsed_time = time.time() - start_time
            print(f"Request {batch_index + 1}/{self.total_requests} completed in {elapsed_time:.2f} seconds.")
            self._append_response(response, batch_index)
        self._finalize_output_file()
        print("All requests have been processed and all responses saved in a single file.")

    def _prepare_messages(self, image_batch):
        messages = []
        for idx, image_file in enumerate(image_batch, start=1):
            image_path = os.path.join(self.image_directory, image_file)
            media_type, base64_data = self.image_to_base64(image_path)
            messages.append({
                "type": "text",
                "text": f"Image {idx}:"
            })
            messages.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data,
                },
            })
        messages.append({
            "type": "text",
            "text": """Analyze the following images from a motorcycle manual. For each image, provide:

                    1. The page number from the top right corner.
                    2. A comprehensive description of the page content, including:
                    a) The main topic or procedure covered
                    b) Any warnings, cautions, or safety information
                    c) Key steps or instructions provided
                    d) Description of diagrams, illustrations, or photos
                    e) Specific parts, tools, or measurements mentioned
                    f) Any technical specifications or torque values
                    g) Cross-references to other sections or pages

                    Aim for a detailed, information-rich description that captures all relevant technical details. Your analysis will be used for a searchable database, so include keywords and phrases a mechanic might use when looking for this information.

                    Do not include the image number in your response. Format your response as follows:

                    Page [Number]: [Detailed description covering all the points mentioned above]

                    Example output:
                    Page 147: This page details the oil filter replacement procedure for the motorcycle engine. It begins with a prominent warning about environmental hazards of improper oil disposal. The main steps include: 1) Removing the old filter, 2) Lubricating the new filter's O-ring, and 3) Installing the new filter. A cross-sectional diagram shows the correct orientation of the filter and O-ring. Tools required: oil filter wrench and torque wrench. The filter cover should be tightened to 10 Nm. Note: Compatible with oil filter models XYZ123 and ABC456. Cross-reference to engine oil change procedure on page 145.
                    """
        })
        return messages

    def _send_request(self, messages):
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="You are a manual writer",
            messages=[
                {
                    "role": "user",
                    "content": messages
                }
            ],
        )
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def _append_response(self, response, batch_index):
        with open(self.output_file_path, "a") as file:
            json.dump(response, file, indent=4)
            if batch_index < self.total_requests - 1:
                file.write(",\n")  # Add a comma between JSON objects

    def _finalize_output_file(self):
        with open(self.output_file_path, "a") as file:
            file.write("]")


