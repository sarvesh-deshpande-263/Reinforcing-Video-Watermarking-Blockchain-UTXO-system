import sys
sys.path.append('C:/Users/SARVESH/Documents/Blockchain')


from BlockChain.backend.core.block import Block
from BlockChain.backend.core.blockheader import BlockHeader
from BlockChain.backend.util.util import hash256, merkle_root
from BlockChain.backend.core.database.database import BlockchainDB
from BlockChain.backend.core.Tx import CoinbaseTx
from multiprocessing import Process, Manager
from BlockChain.frontend.run import main
import time

ZERO_HASH = '0' * 64
VERSION = 1

class BlockChain:

    def __init__(self, utxos, MemPool):
        self.utxos = utxos
        self.MemPool = MemPool

    def write_on_disk(self, block):
        blockchainDB = BlockchainDB()
        blockchainDB.write(block)

    def fetch_last_block(self):
        blockchainDB = BlockchainDB()
        return blockchainDB.lastBlock()
    
    def GenesisBlock(self):
        BlockHeight = 0
        prevBlockHash = ZERO_HASH
        self.addBlock(BlockHeight, prevBlockHash)

    """Keep Track of all the unspent transactions in cache memory for fast retrival"""
    def store_utxos_in_cache(self, Transaction):
        self.utxos[Transaction.TxId] = Transaction

    """Read Transactions from memory pool"""
    def read_transaction_from_memorypool(self):
        self.TxIds = []
        self.addTransactionsInBlock = []
        used_hashes = set()

        blockchainDB = BlockchainDB()
        existing_blocks = blockchainDB.read()
        for block in existing_blocks:
            for tx in block.get("Txs", []):
                if tx.get("videoHash"):
                    used_hashes.add(tx["videoHash"])

        for txid in self.MemPool:
            tx_obj = self.MemPool[txid]
            if hasattr(tx_obj, "videoHash") and tx_obj.videoHash in used_hashes:
                continue 
            if hasattr(tx_obj, "videoHash"):
                used_hashes.add(tx_obj.videoHash)

        for tx in self.MemPool:
            self.TxIds.append(bytes.fromhex(tx))
            self.addTransactionsInBlock.append(self.MemPool[tx])


    """ Remove Transactions from Memory pool """
    def remove_transactions_from_memorypool(self):
        for tx in self.TxIds:
            if tx.hex() in self.MemPool:
                del self.MemPool[tx.hex()]

    def convert_to_json(self):
        self.TxJson = []

        for tx in self.addTransactionsInBlock:
            self.TxJson.append(tx.to_dict())

    def addBlock(self, BlockHeight, prevBlockHash):
        self.read_transaction_from_memorypool()
        timestamp = int(time.time())
        coinbaseInstance = CoinbaseTx(BlockHeight)
        coinbaseTx = coinbaseInstance.CoinbaseTransaction()

        self.TxIds.insert(0, bytes.fromhex(coinbaseTx.TxId))
        self.addTransactionsInBlock.insert(0, coinbaseTx)

        merkleRoot = merkle_root(self.TxIds)[::-1].hex()
        bits = 'ffff001f'
        blockheader = BlockHeader(VERSION, prevBlockHash, merkleRoot, timestamp, bits)
        blockheader.mine()

        self.store_utxos_in_cache(coinbaseTx)
        self.convert_to_json()

        print(f"Block {BlockHeight} mined successfully with Nonce value of {blockheader.nonce}")
        self.write_on_disk([Block(BlockHeight, 1, blockheader.__dict__, 1, self.TxJson).__dict__])

    def main(self):
        lastBlock = self.fetch_last_block()
        if lastBlock is None:
            self.GenesisBlock()
        
        while True:
            lastBlock = self.fetch_last_block()
            BlockHeight = lastBlock["Height"] + 1
            prevBlockHash = lastBlock["BlockHeader"]['blockHash']
            self.addBlock(BlockHeight, prevBlockHash)

if __name__ == "__main__":
    with Manager() as manager:
        utxos = manager.dict()
        MemPool = manager.dict()

        webapp = Process(target = main, args = (utxos, MemPool))
        webapp.start()

        blockchain = BlockChain(utxos, MemPool)
        blockchain.main()