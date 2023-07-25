from destiny.simulation import simulate


def main():
    result = simulate()
    with open("starmap.json", "w") as mapfile:
        mapfile.write(result.model_dump_json())
    print("Done")


if __name__ == "__main__":
    main()
