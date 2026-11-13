// Entrypoint of `npm run generate:wallet -- [network...]`, mainnet when no
// network is named: prints a fresh wallet's secret, so run it only where the
// terminal is private.

import { formatGeneratedWallet, generateWallet, parseNetworks } from "./src/wallet.ts";

console.log(formatGeneratedWallet(generateWallet(parseNetworks(process.argv.slice(2)))));
