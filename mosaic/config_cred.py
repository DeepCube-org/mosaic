from sentinelhub import SHConfig
from argparse import ArgumentParser


if __name__=="__main__":

    parser = ArgumentParser()
    parser.add_argument("--id", type=str, required=True, help="Found at: https://www.sentinel-hub.com/ > Login > User settings > OAuth clients. Copy the ID")
    parser.add_argument("--secret", type=str, required=True, help="Found at: https://www.sentinel-hub.com/ > Login > User settings > OAuth clients. Appears only once after creating a new OAuth client")
    args = parser.parse_args()

    config = SHConfig()
    config.sh_client_id = args.id 
    config.sh_client_secret = args.secret
    config.save("default-profile")

    print(config)

    