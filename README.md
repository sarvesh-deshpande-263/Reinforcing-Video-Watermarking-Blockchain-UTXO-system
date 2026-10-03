# Reinforcing Video Watermarking — Blockchain UTXO System

A UTXO-model blockchain, written from scratch in Python, used as a tamper-evident
registry for video watermark hashes. Registering a watermark means committing its
hash to the chain in a transaction locked to your address; verifying it means
proving that a given hash was registered by the holder of that address.

This is the reference implementation for the paper **"Reinforcing Video Watermarks:
Security Techniques and Blockchain Protocols"**, published by Springer (ICCCT 2025).

---

## Why a blockchain for watermarks

A watermark on its own tells you a video was marked; it does not tell you *who*
marked it or *when*, and both claims rest on trusting whoever stores the record.
Committing the watermark hash to an append-only chain moves that trust into
something independently checkable: the hash is bound to a public-key hash in a
transaction output, so ownership can be verified by anyone holding the chain
without asking the original issuer to vouch for it.

---

## What is implemented

Nothing here is a wrapper around an existing chain. The cryptography, transaction
model and consensus loop are all written in this repository.

| Layer | Contents |
|---|---|
| **Elliptic curve** | `backend/core/EllepticCurve/` — finite-field arithmetic (`FieldElement.py`), curve points and scalar multiplication (`Point.py`), the secp256k1 field (`Sha256Field.py`), signing/verification primitives |
| **Script** | `backend/core/Script.py` — a Bitcoin-style stack script, with `op.py` supplying the opcodes |
| **Transactions** | `backend/core/Tx.py` — transaction construction, serialization and per-input signature verification against the output's `scriptPubKey` |
| **Chain** | `backend/core/blockchain.py`, `block.py`, `blockheader.py` — genesis block, block assembly, the mining loop |
| **Storage** | `backend/core/database/database.py` — file-backed block and account persistence |
| **Client** | `client/account.py`, `client/sendBTC.py` — key/address handling and transaction assembly |
| **Web app** | `frontend/run.py` — a Flask interface with two routes |

### The two flows

**Register** (`/`) — submit a source address and a video hash. The server rejects
the hash if it already exists in the mempool or in a confirmed block, so the same
watermark cannot be registered twice. It then builds a transaction carrying the
hash, verifies every input signature against the script public key, and admits it
to the mempool.

**Verify** (`/verify`) — submit an address and a video hash. The server searches
confirmed blocks first, then the mempool, matching the hash and checking that the
output's script commits to the hash160 of the supplied address. It reports one of
three outcomes: confirmed on-chain, pending in the mempool, or no match.

---

## Running it

Requires Python 3.8+.

```bash
git clone https://github.com/sarvesh-deshpande-263/Reinforcing-Video-Watermarking-Blockchain-UTXO-system.git
cd Reinforcing-Video-Watermarking-Blockchain-UTXO-system

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start the miner and the web app together — the chain loop and the Flask server run
as separate processes sharing a UTXO set and mempool:

```bash
python -m BlockChain.backend.core.blockchain
```

Then open <http://127.0.0.1:5000> for the wallet and
<http://127.0.0.1:5000/verify> for verification.

The repository ships with chain state in `data/`, so verification works on a fresh
clone. Delete `data/blockchain` and `data/account` to mine a new chain from genesis.

---

## Stack

Python · Flask · pycryptodome · qrcode / Flask-QRcode · Pillow

---

## Scope and limitations

Worth stating plainly, since this is research code rather than a product:

- **It is an educational implementation of the primitives.** The elliptic-curve and
  script code was written to demonstrate and measure the protocol in the paper, not
  to be used as a production cryptographic library. Use audited libraries for
  anything real.
- **Consensus is single-node.** The mining loop runs locally; there is no peer
  discovery, no network propagation and no fork-resolution policy.
- **Storage is file-backed**, not a durable or concurrent database.
- **The watermark extraction itself is out of scope here.** This repository covers
  the provenance and verification layer; the watermarking techniques are discussed
  in the paper.

---

## Citation

> "Reinforcing Video Watermarks: Security Techniques and Blockchain Protocols,"
> Springer, ICCCT 2025.

<!-- TODO: add the full author list and the SpringerLink DOI once to hand, e.g.
     https://doi.org/10.1007/... — a resolvable link makes this repo far more
     useful to anyone arriving from the paper (and vice versa). -->


## License

No license file is currently present, which means default copyright applies and the
code is not licensed for reuse. If you want others to build on it, add a license
(MIT or Apache-2.0 are the usual choices for research code).
