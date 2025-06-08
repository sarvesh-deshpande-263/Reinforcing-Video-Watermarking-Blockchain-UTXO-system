from flask import Flask, render_template, request
from BlockChain.backend.core.database.database import BlockchainDB
from BlockChain.backend.util.util import decode_base58
from BlockChain.client.sendBTC import sendBTC
from BlockChain.backend.core.Tx import Tx

app = Flask(__name__)

@app.route('/', methods = ["GET", "POST"])
def wallet():
    message = ''
    if request.method == "POST":
        FromAddress = request.form.get("fromAddress")
        ToAddress = '1NenJbHWoYSKyKpatTAvouqMr3ZzcK7qa5'
        Amount = 1
        VideoHash = request.form.get("videoHash")

        for tx in MEMPOOL.values():
            if hasattr(tx, 'videoHash') and tx.videoHash == VideoHash:
                message = "Duplicate videoHash: already exists in memory pool."
                return render_template('wallet.html', message=message)

        blocks = BlockchainDB().read()
        for block in blocks:
            for tx in block.get('Txs', []):
                if tx.get('videoHash') == VideoHash:
                    message = "Duplicate videoHash: already exists in blockchain."
                    return render_template('wallet.html', message=message)

        sendCoin = sendBTC(FromAddress, ToAddress, Amount, UTXOS, VideoHash)
        TxObj = sendCoin.prepareTransaction()

        script_public_key = sendCoin.scriptPubKey(FromAddress)
        verified = True

        if not TxObj:
            message = "Invalid Transaction"

        if isinstance(TxObj, Tx):
            for index, tx in enumerate(TxObj.tx_ins):
                if not TxObj.verify_input(index, script_public_key):
                    verified = False

            if verified:
                MEMPOOL[TxObj.TxId] = TxObj
                message = "Transaction added in memory pool"


    return render_template('wallet.html', message = message)

@app.route('/verify', methods=["GET", "POST"])
def verify():
    message = ""
    if request.method == "POST":
        fromAddress = request.form.get("fromAddress")
        videoHash = request.form.get("videoHash")

        try:
            h160 = decode_base58(fromAddress)
        except:
            return render_template('verify.html', message="❌ Invalid address.")

        found = False

        # ✅ 1. Check in BlockchainDB (confirmed)
        blocks = BlockchainDB().read()
        for block in blocks:
            for tx in block.get('Txs', []):
                if tx.get('videoHash') == videoHash:
                    for tx_out in tx.get('tx_outs', []):
                        cmds = tx_out.get('script_public_key', {}).get('cmds', [])
                        if len(cmds) >= 3 and cmds[2].lower() == h160.hex().lower():
                            message = "✅ Match found in blockchain (confirmed)."
                            found = True
                            break
            if found:
                break

        # ✅ 2. Check in MEMPOOL (unconfirmed)
        if not found:
            for tx in MEMPOOL.values():
                if hasattr(tx, 'videoHash') and tx.videoHash == videoHash:
                    for tx_out in tx.tx_outs:
                        cmds = tx_out.script_public_key.cmds
                        if len(cmds) >= 3 and cmds[2] == h160:
                            message = "🕓 Match found in mempool (pending confirmation)."
                            found = True
                            break
                if found:
                    break

        if not found:
            message = "❌ No match found for this address and video hash."

    return render_template("verify.html", message=message)


def main(utxos, MemPool):
    global UTXOS
    global MEMPOOL
    UTXOS = utxos
    MEMPOOL = MemPool
    app.run()

