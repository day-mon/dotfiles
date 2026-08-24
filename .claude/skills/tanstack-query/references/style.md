# TanStack Query style

Apply every relevant rule to TanStack Query code. Follow an established project convention before introducing this default structure.

## Organize by API domain

Keep reusable Query code in `src/queries/` when the project has no existing location. Name each module after its API domain or generated API class, such as `src/queries/users.ts` for `UsersApi`.

Co-locate the configured API client, query-key factory, reusable query options, custom hooks, and mutations for one domain. Components consume those exports instead of rebuilding keys or request functions inline.

Reuse a configured API client when the project provides one and the client is safe to share. Do not introduce a client abstraction only to satisfy this style. Keep the request inline when the project makes direct HTTP or SDK calls.

## Define hierarchical keys

Use a domain key factory. Keys are readonly, serializable, and ordered from broad to narrow so invalidation can target one level.

```typescript
export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  list: (filters: UserFilters) => [...userKeys.lists(), filters] as const,
  details: () => [...userKeys.all, "detail"] as const,
  detail: (userId: string) => [...userKeys.details(), userId] as const,
};
```

Include every input that can change the returned data. Reuse the factory for queries, invalidation, cache reads, and cache writes.

## Extract typed query options

Give API functions explicit return types so TanStack Query can infer `data` without call-site generics. Use `queryOptions` to keep the key and query function together while preserving inference across hooks, prefetching, and cache access.

```typescript
import { queryOptions, useQuery } from "@tanstack/react-query";

const client = createConfiguredApiClient(UsersApi);

const userOptions = (userId: string | undefined) =>
  queryOptions({
    queryKey: [...userKeys.details(), userId] as const,
    queryFn: () => client.getUser({ userId: userId! }),
    enabled: !!userId,
    staleTime: millis.fromMinutes(5),
  });

interface UseUserArgs {
  userId: string | undefined;
}

export const useUser = ({ userId }: UseUserArgs) => {
  return useQuery(userOptions(userId));
};
```

When no configured client exists, prefer Ky for an inline HTTP request. Ky throws `HTTPError` for non-2xx responses by default. Pass a Standard Schema to `.json()` so the schema validates and coerces the response.

```typescript
import ky from "ky";

const userOptions = (userId: string | undefined) =>
  queryOptions({
    queryKey: [...userKeys.details(), userId] as const,
    queryFn: () => {
      return ky
        .get(`/api/users/${encodeURIComponent(userId!)}`)
        .json(userSchema);
    },
    enabled: !!userId,
    staleTime: millis.fromMinutes(5),
  });
```

Coercion comes from the supplied schema, not Ky itself. Use schema coercion or transforms when the wire format differs from the application type. If the installed Ky version does not accept a Standard Schema in `.json()`, parse the `unknown` JSON result with the same schema.

Use the project's Ky instance, generated SDK, or HTTP helper when one exists. The inline branch should still return a validated type and throw when the request fails.

Use `enabled: !!value` for conditional queries whose required IDs are non-empty strings. A non-null assertion is acceptable inside the same options object because `enabled` is the runtime gate. Expose manual refetching only after the required input exists. Use an explicit condition when an empty string is a valid input.

Choose `staleTime`, garbage collection, retry, and refetch settings deliberately. Use the project's duration helpers and defaults when they exist.

## Keep fetching out of effects

Use TanStack Query for client-owned asynchronous server state. Do not fetch query data in `useEffect` or mirror query results into local state.

Let a server-first framework own initial reads and server mutations when its framework rules call for that design. Add a client query only when the browser owns refreshing, caching, synchronization, or an interactive mutation flow.

## Define mutations beside their queries

Use `useMutation` for client-owned writes. Accept a named argument object when the mutation has multiple inputs.

```typescript
interface UpdateUserArgs {
  userId: string;
  updates: UpdateUser;
}

export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, updates }: UpdateUserArgs) => {
      return client.updateUser({ userId, user: updates });
    },
    onSuccess: (_data, { userId }) => {
      return queryClient.invalidateQueries({
        queryKey: userKeys.detail(userId),
      });
    },
  });
};
```

Invalidate or update the narrowest affected keys. Return or await invalidation when the mutation should remain pending until fresh data arrives. Use background invalidation only when the interaction does not depend on that refresh.

Use optimistic updates only when immediate feedback matters and rollback is defined. Preserve the previous cache value, restore it on failure, and reconcile with the server result.

## Completion criterion

Before completing Query work, verify domain code is co-located, every result-changing input appears in its key, conditional queries use `enabled: !!value`, inline HTTP uses the project's Ky setup with schema validation, no query fetch runs in an effect, every mutation has an intentional cache strategy, and server-owned data has not been duplicated into a client cache without a reason.
