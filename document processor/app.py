from flask import Flask, request, jsonify, render_template
import requests  # Make sure you have this installed
from datetime import datetime
from util.document_processor import get_vectorstore_from_url, extract_facts


app = Flask(__name__)

processing_status = {
    "question": "",
    "status": "idle",  # Possible values: "idle", "processing", "done"
    "factsByDay": {},
    "removedFacts": {},  # Track removed facts
    "errors": []
}


# Route for the main page
@app.route('/')
def index():
    # Render the main page template
    return render_template('index.html')

# Route for submitting documents
@app.route('/submit_documents', methods=['POST'])
def submit_documents():
    question = request.form['question']
    urls_input = request.form['documents']
    website_urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    auto_approve = 'autoApprove' in request.form

    processing_status["question"] = question
    processing_status["status"] = "processing"
    # Store previous facts to compare with new facts for removals
    previous_facts = processing_status["factsByDay"].copy()
    processing_status["factsByDay"] = {}
    processing_status["errors"] = []

    if auto_approve:
        current_time = datetime.utcnow()

        for url in website_urls:
            try:
                facts_by_date = extract_facts(question, url)
                for date, facts in facts_by_date.items():
                    if date not in processing_status["factsByDay"]:
                        processing_status["factsByDay"][date] = []

                    for fact in facts:
                        existing_facts = [f["fact"] for f in processing_status["factsByDay"].get(date, [])]
                        if fact not in existing_facts:
                            processing_status["factsByDay"][date].append({"fact": fact, "timestamp": current_time.isoformat()})

                # Checking for removed facts
                for date in previous_facts:
                    if date in facts_by_date:
                        new_facts = [f["fact"] for f in processing_status["factsByDay"][date]]
                        for prev_fact in previous_facts[date]:
                            if prev_fact["fact"] not in new_facts:
                                if date not in processing_status["removedFacts"]:
                                    processing_status["removedFacts"][date] = []
                                processing_status["removedFacts"][date].append({"fact": prev_fact["fact"], "timestamp": current_time.isoformat()})

            except Exception as e:
                error_message = f"Error processing document {url}: {str(e)}"
                print(error_message)
                processing_status["errors"].append({"url": url, "error": error_message})

        processing_status["status"] = "done" if not processing_status["errors"] else "partial"
    else:
        processing_status["status"] = "pending"

    return jsonify({"message": "Document processing started."}), 200





# Route for fetching responses based on user input
@app.route('/get_question_and_facts', methods=['GET'])
def get_question_and_facts():


    # Return the processing status as a JSON response
    return jsonify(processing_status), 200


if __name__ == '__main__':
    app.run(debug=True)
