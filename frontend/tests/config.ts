import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

dotenv.config({ path: path.join(__dirname, "../../.env") })

const { FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD } = process.env

// Use default test credentials if not provided in environment
const defaultEmail = "admin@example.com"
const defaultPassword = "changethis"

export const firstSuperuser = (FIRST_SUPERUSER || defaultEmail) as string
export const firstSuperuserPassword = (FIRST_SUPERUSER_PASSWORD || defaultPassword) as string
