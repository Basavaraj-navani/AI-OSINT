from drug_trafficking_osint.infrastructure.slang_engine.dictionary_loader import (
    DictionaryLoader,
)


def main() -> None:
    loader = DictionaryLoader()

    print("=" * 60)
    print("Drug Slang Dictionary Test")
    print("=" * 60)

    print(f"Dictionary Exists : {loader.exists()}")

    entries = loader.load()

    print(f"Entries Loaded    : {len(entries)}")
    print()

    for entry in entries:
        print(f"Drug        : {entry.canonical_name}")
        print(f"Category    : {entry.category}")
        print(f"Risk Weight : {entry.risk_weight}")
        print(f"Aliases     : {', '.join(entry.aliases)}")
        print(f"Hashtags    : {', '.join(entry.hashtags)}")
        print("-" * 60)


if __name__ == "__main__":
    main()
