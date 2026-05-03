import argparse
import yaml
from generator.batch_runner import BatchRunner
from prompt_tool.prompt_generator import PromptGenerator


def cmd_generate_prompts(args):
    cfg = yaml.safe_load(open("config/settings.yaml", "r", encoding="utf-8"))
    examples = [l.strip() for l in open(args.examples, "r", encoding="utf-8") if l.strip()]
    gen = PromptGenerator(
        api_key=cfg["llm"]["api_key"],
        base_url=cfg.get("llm", {}).get("base_url"),
        model=cfg["llm"].get("model", "gpt-4o-mini"),
    )
    prompts = gen.generate(examples, count=args.count)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))
    print(f"Generated {len(prompts)} prompts -> {args.output}")


def cmd_batch_run(args):
    cfg = yaml.safe_load(open("config/settings.yaml", "r", encoding="utf-8"))
    prompts = [l.strip() for l in open(args.prompts, "r", encoding="utf-8") if l.strip()]
    runner = BatchRunner(cfg["comfyui"])
    runner.run(prompts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    p1 = sub.add_parser("gen-prompts", help="Generate prompts with LLM")
    p1.add_argument("--examples", default="prompts/examples.txt")
    p1.add_argument("--output", default="prompts/input_prompts.txt")
    p1.add_argument("--count", type=int, default=100)
    p1.set_defaults(func=cmd_generate_prompts)

    p2 = sub.add_parser("batch-run", help="Run ComfyUI batch generation")
    p2.add_argument("--prompts", default="prompts/input_prompts.txt")
    p2.set_defaults(func=cmd_batch_run)

    args = parser.parse_args()
    args.func(args)
