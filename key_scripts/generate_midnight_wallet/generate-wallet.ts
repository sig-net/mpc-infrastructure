// Entrypoint of `npm run generate:wallet -- [network...]`: prints a fresh
// wallet's secret, so run it only where the terminal is private.

import { formatGeneratedWallet, generateWallet, parseNetworks } from "./src/wallet.ts";

console.log(formatGeneratedWallet(generateWallet(parseNetworks(process.argv.slice(2)))));
