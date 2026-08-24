# React

Apply every relevant rule to React code. Framework-specific rules override data-fetching and server-boundary rules.

## Companion skills and live docs

### UI work

When creating or changing a React UI, invoke the `shadcn` skill before choosing components or writing custom markup. This branch is complete when the skill's project-context, component-search, and component-documentation checks have been applied.

### Forms

Whenever creating, changing, or reviewing a React form, invoke the `react-hook-form` skill. Use React Hook Form for interactive client-side forms. Follow that skill's boundary for trivial native forms, React 19 Server Actions, and server-owned form handling. This branch is complete when the form follows the applicable React Hook Form guidance or the skill identifies the correct non-RHF path.

### TanStack Query

Whenever creating, changing, or reviewing client data work that uses TanStack Query, invoke the `tanstack-query` skill. This branch is complete when its documentation research, query-key, cache, mutation, and validation criteria have been applied.

## Components

Use an arrow function with an explicit `ComponentNameProps` interface. Apply optional defaults while destructuring. Do not use `React.FC` or `defaultProps`.

```tsx
interface UserCardProps {
  user: User;
  onDelete?: (id: string) => void;
  showAvatar?: boolean;
}

const UserCard = ({
  user,
  onDelete,
  showAvatar = true,
}: UserCardProps) => {
  return (
    <article>
      {showAvatar && <Avatar src={user.avatar} />}
      <span>{user.name}</span>
      {onDelete && (
        <button onClick={() => onDelete(user.id)}>Delete</button>
      )}
    </article>
  );
};
```

Type children and slots as `ReactNode`. Type event handlers and refs with their concrete element types.

Keep components focused. Prefer composition to deep prop drilling, and keep data ownership near the component that uses it.

## Hooks

Call hooks at the top level before conditional returns. Extract a custom hook when reusable stateful logic or a component's hook logic becomes hard to scan.

Use a ref with the exact DOM element type. When an external resource depends on the node, set it up in an effect and return cleanup.

## Effects synchronize external systems

Use effects for subscriptions, browser APIs, analytics, manual DOM work, and non-React widgets. Return cleanup for subscriptions and resources.

Keep these operations out of effects:

- Deriving render data. Calculate it during render.
- Responding to user actions. Run that logic in the event handler.
- Resetting a subtree for a new identity. Give the subtree a new `key`.
- Notifying a parent after local state changes. Update local state and call the parent in one handler.
- Caching pure calculations. Let the React compiler handle ordinary memoization when enabled. Use manual memoization only when measurement or an API identity contract requires it.

## Context

Create context with an explicit value type and an `undefined` default. Expose a consumer hook that throws when used outside its provider.

## Directives

Do not add framework directives to framework-neutral React code. In Next.js, add `use client` only at the smallest browser-interactive boundary and use `use server` for Server Actions when required.

Before completing React work, verify every applicable companion branch is complete, every hook is unconditional, each effect synchronizes an external system and cleans up when needed, and component props are explicit.
