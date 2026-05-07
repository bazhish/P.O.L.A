const { spawn } = require("child_process");

function runPython(file, args = []) {
  return new Promise((resolve, reject) => {
    const process = spawn("py", [file, ...args]);

    let output = "";
    let error = "";

    process.stdout.on("data", (data) => {
      output += data.toString();
    });

    process.stderr.on("data", (data) => {
      error += data.toString();
    });

    process.on("close", () => {
      if (error) {
        return reject(error);
      }
      resolve(output.trim());
    });
  });
}

module.exports = runPython;