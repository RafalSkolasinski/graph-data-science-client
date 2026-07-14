# `gds` CLI examples

Sample graphs and ready-to-run job configs for the `gds` command-line tool (see
the [Command-line interface](../../README.md#command-line-interface-gds)
section of the main README). A small selection ported from the
[neo4j-cloud-job-scheduler-prototype](https://github.com/neo4j/neo4j-cloud-job-scheduler-prototype)'s
`gds-testdata`/`gds-runner` examples.

Prereq: `pip install "graphdatascience[cli]"` (or `just install-cli` from the repo
root), and Aura credentials. Copy `env.template` to `.env` in this directory and
fill it in — `gds` auto-loads a `.env` from the current working directory, so run
the commands below from **this `examples/cli/` directory**.

```bash
cp env.template .env
# fill in .env, then run commands from this directory
```

## What's here

Graphs (`graphs/`) and jobs (`jobs/`) share theme names, so they read as a story —
pick a graph, run the matching job:

| Theme | Graph — fixed / random | Job |
| --- | --- | --- |
| social network | `graphs/social-network.json` · `graphs/random-social-network.yaml` | `jobs/social-network-louvain.yaml` → `community` |
| web graph | `graphs/web-graph.json` | `jobs/web-graph-pagerank.yaml` → `pagerank` |

Explicit graphs are `.json` (construct format); random graphs are `.yaml`
(`kind: random` specs). `jobs/built-in/homogeneous.yaml` is a job for the CLI's
built-in generated `homogeneous` graph (`gds database upload homogeneous`).

All jobs share one session (`gds-examples`), so runs reuse it; `--overwrite-graph`
replaces the projected graph each time.

## Run a job (social network)

Three steps — upload a graph, run the job, inspect:

```bash
# fixed graph
gds database upload -f graphs/social-network.json --overwrite
gds session  run --config jobs/social-network-louvain.yaml --overwrite-graph
gds database fetch --label Person        # community column populated

# same job, generated graph
gds database upload -f graphs/random-social-network.yaml --overwrite
gds session  run --config jobs/social-network-louvain.yaml --overwrite-graph
gds database fetch --label Person
```

The web-graph theme follows the same pattern (`--label Page`, `jobs/web-graph-pagerank.yaml`).

## Built-in graph

```bash
gds database upload homogeneous --overwrite
gds session  run --config jobs/built-in/homogeneous.yaml --overwrite-graph
gds database fetch
```

Clean up: `gds database delete --all`. Delete the session when done:
`gds session delete --config jobs/social-network-louvain.yaml`.
