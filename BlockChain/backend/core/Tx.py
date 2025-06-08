import sys
sys.path.append('C:/Users/SARVESH/Documents/Blockchain')
from BlockChain.backend.core.Script import Script
from BlockChain.backend.util.util import int_to_little_endian, bytes_needed, decode_base58, little_endian_to_int, encode_variant, hash256

ZERO_HASH = b'\0' * 32
REWARD = 50

PRIVATE_KEY = '114823047474574241433661738024192665648133529081140970617447421502695454367663'
MINER_ADDRESS = '1JSLKuCZNm6uSogYgZUGLJ9so2QzYJcJg9'
SIGHASH_ALL = 1

class CoinbaseTx:
    def __init__(self, BlockHeight):
        self.BlockHeightInLittleEndian = int_to_little_endian(BlockHeight, bytes_needed(BlockHeight))

    def CoinbaseTransaction(self):
        prev_tx = ZERO_HASH
        prev_index = 0xffffffff

        tx_ins = []
        tx_ins.append(TxIn(prev_tx, prev_index))
        tx_ins[0].script_sig.cmds.append(self.BlockHeightInLittleEndian)


        tx_outs = []
        target_amount = REWARD * 100000000
        target_h160 = decode_base58(MINER_ADDRESS)
        target_script = Script.p2pkh_script(target_h160)
        tx_outs.append(TxOut(amount = target_amount, script_public_key = target_script))
        coinbaseTx = Tx(1, tx_ins, tx_outs, 0)
        coinbaseTx.TxId = coinbaseTx.id()

        return coinbaseTx



class Tx:
    def __init__(self, version, tx_ins, tx_outs, locktime, videoHash = None):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.videoHash = videoHash

    def id(self):
        """Human Readable Tx ID"""
        return self.hash().hex()

    def hash(self):
        """Binary Hash of serialization"""
        return hash256(self.serialize())[::-1]

    def serialize(self):
        result = int_to_little_endian(self.version, 4)
        result += encode_variant(len(self.tx_ins))

        for tx_in in self.tx_ins:
            result += tx_in.serialize()

        result += encode_variant(len(self.tx_outs))

        for tx_out in self.tx_outs:
            result += tx_out.serialize()

        result += int_to_little_endian(self.locktime, 4)

        return result
    
    def sign_hash(self, input_index, script_public_key):
        s = int_to_little_endian(self.version, 4)
        s += encode_variant(len(self.tx_ins))
        for i, tx_in in enumerate(self.tx_ins):
            if i == input_index:
                s += TxIn(tx_in.prev_tx, tx_in.prev_index, script_public_key).serialize()
            else:
                s += TxIn(tx_in.prev_tx, tx_in.prev_index).serialize()

        s += encode_variant(len(self.tx_outs))
        
        for tx_out in self.tx_outs:
            s += tx_out.serialize()

        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGHASH_ALL, 4)
        h256 = hash256(s)

        return int.from_bytes(h256, 'big')

            
    
    def sign_input(self, input_index, private_key, script_public_key):
        z = self.sign_hash(input_index, script_public_key)
        der = private_key.sign(z).der()
        sig = der + SIGHASH_ALL.to_bytes(1, 'big')
        sec = private_key.point.sec()
        self.tx_ins[input_index].script_sig = Script([sig, sec])

    def verify_input(self, input_index, script_public_key):
        tx_in = self.tx_ins[input_index]
        z = self.sign_hash(input_index, script_public_key)
        combined = tx_in.script_sig + script_public_key
        return combined.evaluate(z)



    def is_coinbase(self):
        """
        # Check that there is exactly 1 input
        # Grab the first input and check if prev_tx is b'\x00' * 32
        # Check that the first input prev_index is 0xffffffff
        """

        if len(self.tx_ins) != 1:
            return False
        first_input = self.tx_ins[0]
        if first_input.prev_tx != b'\x00' * 32:
            return False
        
        if first_input.prev_index != 0xffffffff:
            return False
        
        return True

    def to_dict(self):
        """
        Convert Transaction
         # Convert prev_tx Hash in hex from bytes
         # Convert Blockheight in hex which is stored in Script signature
        """

        for tx_index, tx_in in enumerate(self.tx_ins):
            if self.is_coinbase():
                tx_in.script_sig.cmds[0] = little_endian_to_int(tx_in.script_sig.cmds[0])
            tx_in.prev_tx = tx_in.prev_tx.hex()

            for index, cmd in enumerate(tx_in.script_sig.cmds):
                if isinstance(cmd, bytes):
                    tx_in.script_sig.cmds[index] = cmd.hex()

            tx_in.script_sig = tx_in.script_sig.__dict__
            self.tx_ins[tx_index] = tx_in.__dict__

        """
         Convert Transaction Output to dict
          # If there are Numbers we don't need to do anything
          # If values is in bytes, convert it to hex
          # Loop Through all the TxOut Objects and convert them into dict 
        """
        for index, tx_out in enumerate(self.tx_outs):
            tx_out.script_public_key.cmds[2] = tx_out.script_public_key.cmds[2].hex()
            tx_out.script_public_key = tx_out.script_public_key.__dict__
            self.tx_outs[index] = tx_out.__dict__

        tx_dict = self.__dict__.copy()
        tx_dict["videoHash"] = self.videoHash

        return tx_dict   


class TxIn:
    def __init__(self, prev_tx, prev_index, script_sig = None, sequence = 0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index

        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig
        
        self.sequence = sequence

    def serialize(self):
        result = self.prev_tx[::-1]
        result += int_to_little_endian(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_little_endian(self.sequence, 4)
        return result

class TxOut:
    def __init__(self, amount, script_public_key): 
        self.amount = amount
        self.script_public_key = script_public_key

    def serialize(self):
        result = int_to_little_endian(self.amount, 8)
        result += self.script_public_key.serialize()
        return result

