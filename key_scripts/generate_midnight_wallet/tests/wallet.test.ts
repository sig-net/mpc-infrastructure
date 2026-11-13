// The generated wallet against fixed vectors: the addresses the Midnight
// wallet SDK derives for a public test mnemonic, and a DUST public key an MPC
// node derives for the same seed. Pure crypto: no network.

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  dustPublicKeyFromSeed,
  formatGeneratedWallet,
  generateWallet,
  MidnightNetwork,
  parseNetworks,
  walletFromMnemonic,
} from "../src/wallet.ts";

/** The all-zero-entropy BIP-39 test mnemonic, a public value. */
const MNEMONIC = `${"abandon ".repeat(23)}art`;

const SEED_HEX =
  "408b285c123836004f4b8842c89324c1f01382450c0d439af345ba7fc49acf70" +
  "5489c6fc77dbd4e3dc1dd8cc6bc9f043db8ada1e243c4a0eafb290d399480840";

/** The addresses `MNEMONIC` owns, as the Midnight wallet SDK 5.0.0 derives them. */
const ADDRESSES = [
  {
    network: MidnightNetwork.Preview,
    unshielded: "mn_addr_preview19kxg8sxrsty37elmm6yd68tuy7prryjst2r48eapf2fdtd8z4gpq8xczf2",
    dust: "mn_dust_preview1wwd54rhuw4nqajtn34qjslfk0hdc6jlspdkqvvlmmjrsuckpzurpwp4004g",
  },
  {
    network: MidnightNetwork.Preprod,
    unshielded: "mn_addr_preprod19kxg8sxrsty37elmm6yd68tuy7prryjst2r48eapf2fdtd8z4gpq88xj6h",
    dust: "mn_dust_preprod1wwd54rhuw4nqajtn34qjslfk0hdc6jlspdkqvvlmmjrsuckpzurpwqtlugg",
  },
  {
    network: MidnightNetwork.Mainnet,
    unshielded: "mn_addr19kxg8sxrsty37elmm6yd68tuy7prryjst2r48eapf2fdtd8z4gpqunjqeq",
    dust: "mn_dust1wwd54rhuw4nqajtn34qjslfk0hdc6jlspdkqvvlmmjrsuckpzurpw59t5tw",
  },
] as const;

describe("walletFromMnemonic", () => {
  it("gives the mnemonic's 64-byte BIP-39 seed as hex", () => {
    assert.equal(walletFromMnemonic(MNEMONIC, []).seedHex, SEED_HEX);
  });

  for (const expected of ADDRESSES) {
    it(`derives the wallet SDK's addresses on ${expected.network}`, () => {
      assert.deepEqual(walletFromMnemonic(MNEMONIC, [expected.network]).addresses, [expected]);
    });
  }

  it("writes the mnemonic with single spaces", () => {
    assert.equal(walletFromMnemonic(`  ${MNEMONIC.replaceAll(" ", "  ")} `, []).mnemonic, MNEMONIC);
  });

  it("refuses words that are not a BIP-39 mnemonic", () => {
    assert.throws(() => walletFromMnemonic("abandon abandon abandon", []), /Not a valid BIP-39/);
  });
});

describe("dustPublicKeyFromSeed", () => {
  it("derives the DUST key an MPC node derives from the same seed", () => {
    // The first of the DUST key vectors in sig-net/mpc's chain-midnight funding tests.
    assert.equal(
      dustPublicKeyFromSeed(Buffer.from("04".repeat(32), "hex")).toString(16),
      "115db88b665025219c371ad48289cc6b274bccc6baa8b52fd6f7ada315e030c0",
    );
  });
});

describe("generateWallet", () => {
  it("generates a different 24-word mnemonic each time", () => {
    const first = generateWallet([]);
    const second = generateWallet([]);
    assert.equal(first.mnemonic.split(" ").length, 24);
    assert.notEqual(second.mnemonic, first.mnemonic);
  });
});

describe("formatGeneratedWallet", () => {
  it("writes the seed words, the seed hex and each network's addresses", () => {
    assert.equal(
      formatGeneratedWallet({
        mnemonic: "one two three",
        seedHex: "abcd",
        addresses: [
          {
            network: MidnightNetwork.Preprod,
            unshielded: "mn_addr_x",
            dust: "mn_dust_z",
          },
        ],
      }),
      [
        "Seed Words: one two three",
        "Seed Hex: abcd",
        "",
        "Addresses on preprod:",
        "  Unshielded (NIGHT): mn_addr_x",
        "  Dust: mn_dust_z",
      ].join("\n"),
    );
  });
});

describe("parseNetworks", () => {
  it("names mainnet when none is given", () => {
    assert.deepEqual(parseNetworks([]), ["mainnet"]);
  });

  it("keeps the named networks in the order given", () => {
    assert.deepEqual(parseNetworks(["mainnet", "preprod"]), ["mainnet", "preprod"]);
  });

  it("refuses a name that is not a network", () => {
    assert.throws(
      () => parseNetworks(["preprod", "stagenet"]),
      /Unknown network "stagenet": expected one of preview, preprod, mainnet\./,
    );
  });
});
