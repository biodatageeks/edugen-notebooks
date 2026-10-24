version 1.0

workflow scatter_demo {
    # Tablice, po których będziemy iterować
    input {
        Array[String] samples = ["mother", "father", "son"]
        Array[String] regions = ["chr20:1-500000", "chr20:500001-1000000"]
    }

    # 1. Prosty scatter: jedna instancja zadania (shard) dla każdego elementu tablicy
    scatter (sample in samples) {
        call SayHello { input: name = sample }
    }
    # Poza blokiem scatter SayHello.message ma typ Array[String] (niejawny gather)

    # 2. Zagnieżdżony scatter: każda próbka x każdy region
    scatter (sample in samples) {
        scatter (region in regions) {
            call ProcessRegion { input: sample = sample, region = region }
        }
    }
    # Poza oboma blokami ProcessRegion.result ma typ Array[Array[String]]

    # 3. To samo za pomocą cross(): jeden scatter po parach (Pair) próbka-region
    scatter (pair in cross(samples, regions)) {
        call ProcessRegion as ProcessPair { input: sample = pair.left, region = pair.right }
    }
    # ProcessPair.result ma typ Array[String]

    # 4. Gather: scalenie wyników wszystkich shardów w jednym zadaniu
    call Gather { input: lines = flatten(ProcessRegion.result) }

    output {
        Array[String] greetings = SayHello.message
        Array[String] pairs = ProcessPair.result
        File summary = Gather.summary
    }
}

task SayHello {
    input {
        String name
    }

    command <<<
        echo "Hello ~{name}"
    >>>

    output {
        String message = read_string(stdout())
    }
}

task ProcessRegion {
    input {
        String sample
        String region
    }

    command <<<
        echo "Przetwarzam próbkę ~{sample} w regionie ~{region}"
    >>>

    output {
        String result = read_string(stdout())
    }
}

task Gather {
    input {
        Array[String] lines
    }

    # write_lines() zapisuje tablicę do pliku, po jednym elemencie w linii
    command <<<
        cat ~{write_lines(lines)} > summary.txt
    >>>

    output {
        File summary = "summary.txt"
    }
}
