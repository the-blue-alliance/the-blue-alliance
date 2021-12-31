import argparse


parser = argparse.ArgumentParser(
    description="Create deafult users in the Firebase authentication emulator."
)
parser.add_argument(
    "--project", dest="project", required=True, help="project ID for auth emulator"
)
parser.add_argument(
    "--emulator-host",
    dest="emulator_host",
    default="localhost:9099",
    help="hostname + port for auth emulator (default: localhost:9099)",
)


def main():
    args = parser.parse_args()

    import os

    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = args.emulator_host

    import firebase_admin

    firebase_admin.initialize_app(options={"projectId": args.project})

    from firebase_admin import auth

    admin_uid = "1"
    admin_email = "admin@thebluealliance.com"
    admin_name = "TBA Admin"
    admin_record = auth.ImportUserRecord(
        admin_uid,
        email=admin_email,
        display_name=admin_name,
        provider_data=[
            auth.UserProvider(
                admin_uid,
                provider_id="google.com",
                email=admin_email,
                display_name=admin_name,
            ),
            auth.UserProvider(
                admin_uid,
                provider_id="apple.com",
                email=admin_email,
                display_name=admin_name,
            ),
        ],
        custom_claims={"admin": True},
    )

    user_uid = "2"
    user_email = "user@thebluealliance.com"
    user_name = "TBA User"
    user_record = auth.ImportUserRecord(
        user_uid,
        email=user_email,
        display_name=user_name,
        provider_data=[
            auth.UserProvider(
                user_uid,
                provider_id="google.com",
                email=user_email,
                display_name=user_name,
            ),
            auth.UserProvider(
                user_uid,
                provider_id="apple.com",
                email=user_email,
                display_name=user_name,
            ),
        ],
        custom_claims={},
    )

    auth.import_users([admin_record, user_record])


if __name__ == "__main__":
    main()
