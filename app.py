from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import subprocess
from zipfile import ZipFile
import uuid
import re
import shutil

app = Flask(__name__)
app.config["ENV"] = "production"
app.config["SECRET_KEY"] = "c79157e0275feca1d9d36d05841e87e31dce375144b2f9726a9e598f3b25fd5a"

if Path("temp_folder").exists():
    shutil.rmtree(Path("temp_folder"))
    Path("temp_folder").mkdir(exist_ok=True, parents=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    else:
        valid_assign_numbers = [1, 2]

        assignment_number = int(request.form.get("assign_number")) if request.form.get("assign_number") else 0
        if assignment_number not in valid_assign_numbers:
            flash("Invalid assignment number.")
            return redirect(url_for("show_errors"))

        uploaded_file = request.files.get("code_file")

        if not uploaded_file:
            flash("No file uploaded.")
            return redirect(url_for("show_errors"))

        if not bool(re.match(r"^[A-Z][a-z]+_800\d{6}.zip$", uploaded_file.filename)):
            flash("Invalid zip file name. Should be Lastname_AggieID.zip")
            return redirect(url_for("show_errors"))

        unique_id = uuid.uuid4().hex
        save_dir = Path("temp_folder", f"{unique_id}")
        save_dir.mkdir(exist_ok=True, parents=True)

        try:
            uploaded_file.save(Path(save_dir, uploaded_file.filename))

            with ZipFile(Path(save_dir, uploaded_file.filename), "r") as zip_file:

                if zip_file.namelist() not in [[f"assignment{assignment_number}.{ext}"] for ext in ["py", "cpp", "java"]]:
                    flash(f"Zip file does not contain assignment{assignment_number}.py or .cpp or .java")
                    return redirect(url_for("show_errors"))

                zip_file.extractall(Path(save_dir, Path(uploaded_file.filename).stem))

            prog_out = subprocess.run(
                [
                    "python",
                    Path("..", "CS372_Code_Grader", "main.py").absolute(),
                    str(assignment_number),
                    save_dir.absolute(),
                    "console"
                ],
                cwd=Path("..", "CS372_Code_Grader").absolute(),
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )

            shutil.rmtree(save_dir)

            prog_stdout = prog_out.stdout.replace("\n", "<br>").replace("\t", "    ") if prog_out.stdout else ""
            prog_stderr = prog_out.stderr.replace("\n", "<br>").replace("\t", "    ") if prog_out.stderr else ""

            flash(prog_stdout, "prog_stdout")
            flash(prog_stderr, "prog_stderr")

            return redirect(url_for("show_results"))

        except Exception as e:
            flash(repr(e))
            return redirect(url_for("show_errors"))


@app.route("/results", methods=["GET"])
def show_results():
    return render_template("results.html")


@app.route("/error", methods=["GET"])
def show_errors():
    return render_template("error.html")
