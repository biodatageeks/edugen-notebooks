# Example workflow
version 1.0
workflow test {
    call TestTask
}

task myTask {
    command <<<
        echo "hello world"
    >>>
    output {
        String out = read_string(stdout())
    }
}