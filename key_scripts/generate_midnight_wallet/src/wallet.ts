// Midnight wallet generation: a fresh BIP-39 mnemonic, its seed in hex, and
// the addresses that seed owns on each nominated network. Pure crypto: no
// network. The DUST key is the one an MPC node derives from the same seed for
// its funding wallet (BIP-32 `m/44'/2400'/0'/2/0`).

import * as ledger from "@midnightntwrk/ledger-v9";
import {
  DustAddress,
  MidnightBech32m,
  UnshieldedAddress,
} from "@midnightntwrk/wallet-sdk-address-format";
import { WalletSeeds } from "@midnightntwrk/wallet-sdk-hd";
import * as bip39 from "@scure/bip39";
import { wordlist as english } from "@scure/bip39/wordlists/english.js";

/**
 * Generate a wallet from a fresh random 24-word mnemonic.
 *
 * @param networks - The networks to derive the wallet's addresses for.
 * @returns The mnemonic, its seed in hex and the addresses per network.
 */
export function generateWallet(networks: readonly MidnightNetwork[]): GeneratedWallet {
  return walletFromMnemonic(bip39.generateMnemonic(english, 256), networks);
}

/** The deployed Midnight networks an MPC node can serve. */
export enum MidnightNetwork {
  Preview = "preview",
  Preprod = "preprod",
  Mainnet = "mainnet",
}

/** A wallet's secret in both spellings and the addresses it owns. */
export interface GeneratedWallet {
  /** The BIP-39 mnemonic, its words separated by single spaces. */
  readonly mnemonic: string;
  /** The mnemonic's 64-byte BIP-39 seed as lowercase hex, which derives the same wallet as the mnemonic. */
  readonly seedHex: string;
  /** The wallet's addresses on each requested network, in the order requested. */
  readonly addresses: readonly NetworkAddresses[];
}

/** One network's encoding of a wallet's addresses. */
export interface NetworkAddresses {
  /** The network the addresses are encoded for. */
  readonly network: MidnightNetwork;
  /** The address NIGHT is received at. */
  readonly unshielded: string;
  /** The address NIGHT is registered to for DUST generation. */
  readonly dust: string;
}

/**
 * Describe the wallet a mnemonic owns: its seed in hex and its addresses on
 * each network.
 *
 * @param mnemonic - A BIP-39 mnemonic.
 * @param networks - The networks to derive the wallet's addresses for.
 * @returns The mnemonic, its seed in hex and the addresses per network.
 * @throws {Error} If `mnemonic` is not a valid BIP-39 mnemonic.
 */
export function walletFromMnemonic(
  mnemonic: string,
  networks: readonly MidnightNetwork[],
): GeneratedWallet {
  const words = mnemonic.trim().split(/\s+/).join(" ");
  if (!bip39.validateMnemonic(words, english)) {
    throw new Error("Not a valid BIP-39 mnemonic.");
  }
  const seed = bip39.mnemonicToSeedSync(words);
  return {
    mnemonic: words,
    seedHex: Buffer.from(seed).toString("hex"),
    addresses: networks.map((network) => addressesFromSeed(seed, network)),
  };
}

/**
 * Derive a seed's addresses on one network, the way the Midnight wallet SDK
 * derives them: account 0, index 0 of each role.
 *
 * @param seed - The wallet's seed, 16 to 64 bytes.
 * @param network - The network the addresses are encoded for.
 * @returns The unshielded and dust addresses.
 */
export function addressesFromSeed(seed: Uint8Array, network: MidnightNetwork): NetworkAddresses {
  const seeds = WalletSeeds.fromMasterSeed(seed);
  const verifyingKey = ledger.signatureVerifyingKey({
    tag: "schnorr",
    value: Buffer.from(seeds.unshielded).toString("hex"),
  });
  return {
    network,
    unshielded: MidnightBech32m.encode(
      network,
      new UnshieldedAddress(Buffer.from(ledger.addressFromKey(verifyingKey), "hex")),
    ).asString(),
    dust: DustAddress.encodePublicKey(network, dustPublicKeyFromSeed(seed)),
  };
}

/**
 * The DUST public key of a seed's account 0, index 0.
 *
 * @param seed - The wallet's seed, 16 to 64 bytes.
 * @returns The public key.
 */
export function dustPublicKeyFromSeed(seed: Uint8Array): bigint {
  return ledger.DustSecretKey.fromSeed(WalletSeeds.fromMasterSeed(seed).dust).publicKey;
}

/**
 * Write a generated wallet for the terminal: the seed words, the seed in
 * hex, then each network's addresses.
 *
 * @param wallet - The wallet to write.
 * @returns The report, as newline-joined lines.
 */
export function formatGeneratedWallet(wallet: GeneratedWallet): string {
  return [
    `Seed Words: ${wallet.mnemonic}`,
    `Seed Hex: ${wallet.seedHex}`,
    ...wallet.addresses.flatMap(({ network, unshielded, dust }) => [
      "",
      `Addresses on ${network}:`,
      `  Unshielded (NIGHT): ${unshielded}`,
      `  Dust: ${dust}`,
    ]),
  ].join("\n");
}

/**
 * Read the networks named on a command line.
 *
 * @param names - The network names as typed, e.g. `["preprod", "mainnet"]`.
 * @returns The named networks in the order given, or mainnet when none is named.
 * @throws {Error} If a name is not a network.
 */
export function parseNetworks(names: readonly string[]): readonly MidnightNetwork[] {
  if (names.length === 0) return [MidnightNetwork.Mainnet];
  const known = Object.values(MidnightNetwork);
  return names.map((name) => {
    const network = known.find((candidate) => candidate === name);
    if (network === undefined) {
      throw new Error(`Unknown network "${name}": expected one of ${known.join(", ")}.`);
    }
    return network;
  });
}
