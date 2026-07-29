export const API_MOCK_ENV = "NEXT_PUBLIC_API_MOCK";

export function isApiMockEnabled(
  env?: Record<string, string | undefined>,
): boolean {
  const flag = env?.[API_MOCK_ENV] ?? process.env.NEXT_PUBLIC_API_MOCK;
  return flag === "1";
}
