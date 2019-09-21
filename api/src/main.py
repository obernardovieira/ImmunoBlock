import datetime
import sys
import json
import os
import shutil

import maya

from nucypher.characters.lawful import Bob, Ursula
from nucypher.config.characters import AliceConfiguration
from nucypher.utilities.logging import GlobalLoggerSettings

# flask
from flask import Flask
app = Flask(__name__)

######################
# Boring setup stuff #
######################


# Twisted Logger
from nucypher.utilities.sandbox.constants import TEMPORARY_DOMAIN

GlobalLoggerSettings.start_console_logging()

TEMP_ALICE_DIR = os.path.join('/', 'tmp', 'heartbeat-demo-alice')


# if your ursulas are NOT running on your current host,
# run like this: python alicia.py 172.28.1.3:11500
# otherwise the default will be fine.

try:
    SEEDNODE_URI = sys.argv[1]
except IndexError:
    SEEDNODE_URI = "172.28.1.4:11500"

POLICY_FILENAME = "policy-metadata.json"

# endpoints

@app.route('/grant')
def grantAccess():
    #######################################
    # Alicia, the Authority of the Policy #
    #######################################


    # We get a persistent Alice.
    # If we had an existing Alicia in disk, let's get it from there

    passphrase = "TEST_ALICIA_INSECURE_DEVELOPMENT_PASSWORD"
    # If anything fails, let's create Alicia from scratch
    # Remove previous demo files and create new ones

    shutil.rmtree(TEMP_ALICE_DIR, ignore_errors=True)

    ursula = Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI,
                                            federated_only=True,
                                            minimum_stake=0)

    alice_config = AliceConfiguration(
        config_root=os.path.join(TEMP_ALICE_DIR),
        domains={TEMPORARY_DOMAIN},
        known_nodes={ursula},
        start_learning_now=False,
        federated_only=True,
        learn_on_same_thread=True,
    )

    alice_config.initialize(password=passphrase)

    alice_config.keyring.unlock(password=passphrase)
    alicia = alice_config.produce()

    # We will save Alicia's config to a file for later use
    alice_config_file = alice_config.to_configuration_file()

    # Let's get to learn about the NuCypher network
    alicia.start_learning_loop(now=True)

    # At this point, Alicia is fully operational and can create policies.
    # The Policy Label is a bytestring that categorizes the data that Alicia wants to share.
    # Note: we add some random chars to create different policies, only for demonstration purposes
    label = "heart-data-❤️-"+os.urandom(4).hex()
    label = label.encode()

    # Alicia can create the public key associated to the policy label,
    # even before creating any associated policy.
    policy_pubkey = alicia.get_policy_encrypting_key_from_label(label)

    print("The policy public key for "
        "label '{}' is {}".format(label.decode("utf-8"), policy_pubkey.to_bytes().hex()))

    # Data Sources can produce encrypted data for access policies
    # that **don't exist yet**.
    # In this example, we create a local file with encrypted data, containing
    # heart rate measurements from a heart monitor
    import heart_monitor
    heart_monitor.generate_heart_rate_samples(policy_pubkey,
                                            samples=50,
                                            save_as_file=True)


    # Alicia now wants to share data associated with this label.
    # To do so, she needs the public key of the recipient.
    # In this example, we generate it on the fly (for demonstration purposes)
    from doctor_keys import get_doctor_pubkeys
    doctor_pubkeys = get_doctor_pubkeys()

    # We create a view of the Bob who's going to be granted access.
    doctor_strange = Bob.from_public_keys(verifying_key=doctor_pubkeys['sig'],
                                        encrypting_key=doctor_pubkeys['enc'],
                                        federated_only=True)

    # Here are our remaining Policy details, such as:
    # - Policy expiration date
    policy_end_datetime = maya.now() + datetime.timedelta(days=5)
    # - m-out-of-n: This means Alicia splits the re-encryption key in 5 pieces and
    #               she requires Bob to seek collaboration of at least 3 Ursulas
    m, n = 2, 3


    # With this information, Alicia creates a policy granting access to Bob.
    # The policy is sent to the NuCypher network.
    print("Creating access policy for the Doctor...")
    policy = alicia.grant(bob=doctor_strange,
                        label=label,
                        m=m,
                        n=n,
                        expiration=policy_end_datetime)
    print("Done!")

    # For the demo, we need a way to share with Bob some additional info
    # about the policy, so we store it in a JSON file
    policy_info = {
        "policy_pubkey": policy.public_key.to_bytes().hex(),
        "alice_sig_pubkey": bytes(alicia.stamp).hex(),
        "label": label.decode("utf-8"),
    }

    filename = POLICY_FILENAME
    with open(filename, 'w') as f:
        json.dump(policy_info, f)

    return "Hello World!"

@app.route('/revoke')
def revokeAccess():
    # TODO: path joins?
    TEMP_DOCTOR_DIR = "{}/doctor-files".format(os.path.dirname(os.path.abspath(__file__)))

    # Remove previous demo files and create new ones
    shutil.rmtree(TEMP_DOCTOR_DIR, ignore_errors=True)

    ursula = Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI,
                                            federated_only=True,
                                            minimum_stake=0)

    # To create a Bob, we need the doctor's private keys previously generated.
    from doctor_keys import get_doctor_privkeys

    doctor_keys = get_doctor_privkeys()

    bob_enc_keypair = DecryptingKeypair(private_key=doctor_keys["enc"])
    bob_sig_keypair = SigningKeypair(private_key=doctor_keys["sig"])
    enc_power = DecryptingPower(keypair=bob_enc_keypair)
    sig_power = SigningPower(keypair=bob_sig_keypair)
    power_ups = [enc_power, sig_power]

    print("Creating the Doctor ...")

    doctor = Bob(
        domains={TEMPORARY_DOMAIN},
        federated_only=True,
        crypto_power_ups=power_ups,
        start_learning_now=True,
        abort_on_learning_error=True,
        known_nodes=[ursula],
        save_metadata=False,
        network_middleware=RestMiddleware(),
    )

    print("Doctor = ", doctor)

    # Let's join the policy generated by Alicia. We just need some info about it.
    with open("policy-metadata.json", 'r') as f:
        policy_data = json.load(f)

    policy_pubkey = UmbralPublicKey.from_bytes(bytes.fromhex(policy_data["policy_pubkey"]))
    alices_sig_pubkey = UmbralPublicKey.from_bytes(bytes.fromhex(policy_data["alice_sig_pubkey"]))
    label = policy_data["label"].encode()

    print("The Doctor joins policy for label '{}'".format(label.decode("utf-8")))
    doctor.join_policy(label, alices_sig_pubkey)

    # Now that the Doctor joined the policy in the NuCypher network,
    # he can retrieve encrypted data which he can decrypt with his private key.
    # But first we need some encrypted data!
    # Let's read the file produced by the heart monitor and unpack the MessageKits,
    # which are the individual ciphertexts.
    data = msgpack.load(open("heart_data.msgpack", "rb"), raw=False)
    message_kits = (UmbralMessageKit.from_bytes(k) for k in data['kits'])

    # The doctor also needs to create a view of the Data Source from its public keys
    data_source = Enrico.from_public_keys(
        verifying_key=data['data_source'],
        policy_encrypting_key=policy_pubkey
    )

    # Now he can ask the NuCypher network to get a re-encrypted version of each MessageKit.
    for message_kit in message_kits:
        try:
            start = timer()
            retrieved_plaintexts = doctor.retrieve(
                label=label,
                message_kit=message_kit,
                data_source=data_source,
                alice_verifying_key=alices_sig_pubkey
            )
            end = timer()

            plaintext = msgpack.loads(retrieved_plaintexts[0], raw=False)

            # Now we can get the heart rate and the associated timestamp,
            # generated by the heart rate monitor.
            heart_rate = plaintext['heart_rate']
            timestamp = maya.MayaDT(plaintext['timestamp'])

            # This code block simply pretty prints the heart rate info
            terminal_size = shutil.get_terminal_size().columns
            max_width = min(terminal_size, 120)
            columns = max_width - 12 - 27
            scale = columns / 40
            scaled_heart_rate = int(scale * (heart_rate - 60))
            retrieval_time = "Retrieval time: {:8.2f} ms".format(1000 * (end - start))
            line = ("-" * scaled_heart_rate) + "❤︎ ({} BPM)".format(heart_rate)
            line = line.ljust(max_width - 27, " ") + retrieval_time
            print(line)
        except Exception as e:
            # We just want to know what went wrong and continue the demo
            traceback.print_exc()

    return "Hello World!"

if __name__ == '__main__':
    app.run()
