"""Integration code for VaderModularFuzzer."""

import os
import shutil
import subprocess

from fuzzers import utils

def build():  # pylint: disable=too-many-branches,too-many-statements
    """Build benchmark."""
    build_directory = os.environ["OUT"]

    os.environ["CC"] = "/usr/bin/afl-clang-fast"
    os.environ["CXX"] = "/usr/bin/afl-clang-fast++"

    os.environ["FUZZER_LIB"] = "/libAFLDriver.a"

    # os.environ["AFL_QUIET"] = "1"
    # os.environ["AFL_MAP_SIZE"] = "2621440"

    src = os.getenv("SRC")
    work = os.getenv("WORK")

    with utils.restore_directory(src), utils.restore_directory(work):
        # Restore SRC to its initial state so we can build again without any
        # trouble. For some OSS-Fuzz projects, build_benchmark cannot be run
        # twice in the same directory without this.
        utils.build_benchmark()

    shutil.copytree(
        "/vadermodularfuzzer/build/vmf_install/",
        f"{build_directory}/vmf_install/")

def remove_zero_byte_files(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
            try:
                os.remove(file_path)
                # print(f"Removed zero-byte file: {filename}")
            except OSError as e:
                continue
                # print(f"Error removing file: {filename}, {e}")
        elif os.path.isfile(file_path):
            continue
            # print(f"{file_path} : {os.path.getsize(file_path)}")
        else:
            # print(f"DIRECTORY: {file_path} : {os.path.getsize(file_path)}")
            shutil.rmtree(file_path, ignore_errors=True)

# pylint: disable=too-many-arguments
def fuzz(input_corpus,
         output_corpus,
         target_binary,
         flags=tuple()):  # pylint: disable=too-many-arguments
    """Run fuzzer."""
    # print(f'Input Corpus: {input_corpus}')
    # target_binary_directory = os.path.dirname(target_binary)

    target_binary_name = os.path.basename(target_binary)

    benchmark_template_path = \
        "/out/vmf_install/test/haystackSUT/"

    benchmark_template = f"{benchmark_template_path}haystack_file.yaml"

    benchmark_config = f"{benchmark_template_path}{target_binary_name}.yaml"
    default_config = "/out/vmf_install/test/config/defaultModules.yaml"

    shutil.copy2(benchmark_template,benchmark_config)

    flags_str = '", "'.join(list(flags))
    # print(f'Flags: {flags_str}')
    #
    result = subprocess.run("ls /out/seeds | wc -l", shell=True, check=True, capture_output=True, text=True)

    if not int(result.stdout.strip()):
        # no seeds - use strings initialization
        subprocess.run(["sed",
                        "-i",
                        "s/#- className: StringsInitialization/- className: StringsInitialization/g",
                        default_config],
                       check=True)
        subprocess.run(["sed",
                        "-i",
                        "s/- className: DirectoryBasedSeedGen/#- className: DirectoryBasedSeedGen/g",
                        default_config],
                       check=True)
        subprocess.run(["sed",
                        "-i",
                        "s/DirectoryBasedSeedGen/StringsInitialization/g",
                        benchmark_config],
                       check=True)
        subprocess.run(["sed",
                        "-i",
                        "s/inputDir: \*INPUT_DIR/sutArgv: \*SUT_ARGV/g",
                        benchmark_config],
                       check=True)
    else:
        # replace input directory
        subprocess.run(["sed",
                        "-i",
                        f"s:test/haystackSUT/test-input/:{input_corpus}:g",
                        benchmark_config],
                       check=True)
    # print("Result of ls = " + result.stdout)

    remove_zero_byte_files(f"{input_corpus}")

    # replace SUT value
    subprocess.run(["sed",
                    "-i",
                    f"s:test/haystackSUT/haystack:{target_binary}:g",
                    benchmark_config],
                   check=True)

    # replace SUT flags
    if flags_str:
        subprocess.run(["sed",
                        "-i",
                        f"s/@@/{flags_str}/g",
                        benchmark_config],
                       check=True)


    # replace output directory
    subprocess.run(["sed",
                    "-i",
                    f"s#: output#: {output_corpus}#g",
                    benchmark_config],
                   check=True)

    cmd = [
        "/out/vmf_install/bin/vader",
        "-c",
        "/out/vmf_install/test/config/defaultModules.yaml",
        "-c",
        f"{benchmark_config}",
    ]

    # print(f"{' '.join(cmd)}")

    subprocess.call(cmd)
