<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IV Data Processing and Analysis</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
        }

        h1, h2, h3, h4, h5, h6 {
            font-weight: bold;
        }

        h2 {
            margin-top: 1.5em;
        }

        a {
            color: #1a0dab;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        pre {
            background-color: #f8f8f8;
            border: 1px solid #cccccc;
            padding: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        code {
            font-family: Consolas, Monaco, Lucida Console, monospace;
        }

        ul {
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <h1>IV Data Processing and Analysis</h1>

    <p>This folder contains codes to read, process, and analyze IV data from potentiostats. The data processing pipeline can handle multiple file formats and encodings, and it provides useful information about the input data, such as axis crossing points.</p>

    <h2>Table of Contents</h2>
    <ul>
        <li><a href="#usage">Usage</a></li>
        <li><a href="#modules">Modules</a></li>
        <li><a href="#contributing">Contributing</a></li>
        <li><a href="#license">License</a></li>
    </ul>

    <h2 id="usage">Usage</h2>

    <ol>
        <li>Make sure you have the necessary Python packages installed, such as pandas and NumPy.</li>
        <li>Place your raw data files in a directory.</li>
        <li>Run the main script using the following command, specifying the path to your data directory:<br><pre>python main.py --path /path/to/your/data-directory</pre></li>
        <li>The program will read and process the data, providing useful information and storing the results in a structured format.</li>
    </ol>

    <h2 id="modules">Modules</h2>

    <ul>
        <li><code>main.py</code>: The main entry point of the program, providing a user-friendly interface to interact with the data processing pipeline.</li>
        <li><code>instruments.py</code>: Contains utility functions and classes for working with instrument data, such as data filtering, interpolation, and axis crossing detection.</li>
        <li><code>read_iv.py</code>: Contains the <code>ReadData</code> class, which reads and parses raw data from different potentiostats, and gathers metadata for logging purposes.</li>
    </ul>

    <h2 id="contributing">Contributing</h2>

    <p>Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.</p>

    <h2 id="license">License</h2>

    <p><a href="https://choosealicense.com/licenses/mit/">MIT License</a></p>
</body>
</html>
