# typescript react patterns

## component declaration

use arrow functions with explicit `ComponentNameProps` type.

```typescript
// good
interface UserCardProps {
  user: User;
  onDelete?: (id: string) => void;
  showAvatar?: boolean;
}

const UserCard = ({ user, onDelete, showAvatar = true }: UserCardProps) => {
  return (
    <div>
      {showAvatar && <Avatar src={user.avatar} />}
      <span>{user.name}</span>
      {onDelete && <button onClick={() => onDelete(user.id)}>delete</button>}
    </div>
  );
};

// bad — no props type
const UserCard = (props) => { ... }

// bad — fc type
const UserCard: FC<UserCardProps> = (props) => { ... }
```

## default props

destructuring defaults. no `defaultProps`.

```typescript
interface ButtonProps {
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  onClick: () => void;
}

const Button = ({
  variant = "primary",
  size = "md",
  disabled = false,
  onClick
}: ButtonProps) => {
  ...
};
```

## hooks rules

top-level only. no conditionals before hooks.

```typescript
// good
const UserList = ({ users }: UserListProps) => {
  const [filter, setFilter] = useState("");
  const filtered = useMemo(() =>
    users.filter(u => u.name.includes(filter)),
    [users, filter]
  );

  if (users.length === 0) return <Empty />;

  return ...
};

// bad — conditional before hook
const UserList = ({ users }: UserListProps) => {
  if (users.length === 0) return <Empty />; // breaks rules of hooks

  const [filter, setFilter] = useState("");
  ...
};
```

## data fetching — use react-query

**never fetch in useEffect.** always use tanstack query via custom hooks in `src/queries/`.

```typescript
// bad — fetching in useEffect
useEffect(() => {
  const fetchData = async () => {
    const result = await api.get(userId);
    setUser(result);
  };
  fetchData();
}, [userId]);

// good — use custom query hook
const { data: user, isLoading, isError } = useUser({ userId });
```

## useeffect patterns

use sparingly. for non-data side effects only: subscriptions, manual dom, analytics.

```typescript
// good — subscription
useEffect(() => {
  const ws = new WebSocket(url);
  ws.onmessage = handleMessage;
  return () => ws.close();
}, [url]);

// bad — missing deps
useEffect(() => { ... }); // runs every render

// bad — async directly
useEffect(async () => { ... }, []);
```

## query hooks

custom hooks live in `src/queries/` named after the api class.

```typescript
// src/queries/users.ts
import { useQuery } from "@tanstack/react-query";

const client = createConfiguredApiClient(UsersApi);

export const userKeys = {
  all: ["users"] as const,
  byId: (id: string) => [...userKeys.all, id] as const,
};

export const useUser = ({ userId }: { userId: string | undefined }) => {
  return useQuery({
    queryKey: userKeys.byId(userId!),
    queryFn: () => client.getUser({ userId: userId! }),
    enabled: !!userId,
    staleTime: millis.fromMinutes(5),
  });
};
```

## mutations

use `useMutation` for writes. invalidate queries in `onSuccess` or `onSettled`.

```typescript
export const useUpdateUser = () => {
  return useMutation({
    mutationFn: ({ userId, updates }) =>
      client.updateUser({ userId, user: updates }),
    onSuccess: (_data, { userId }) => {
      void queryClient.invalidateQueries({ queryKey: userKeys.byId(userId) });
    },
  });
};
```

## event handlers

type explicitly or inline. extract if shared.

```typescript
// inline — simple
<button onClick={(e) => handleClick(e)}>go</button>

// typed handler
const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  ...
};

// typed with custom events
type ChangeHandler = ChangeEvent<HTMLInputElement>;
const onChange = (e: ChangeHandler) => setValue(e.target.value);
```

## children

use explicit `ReactNode` type, default to optional.

```typescript
interface LayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
}

const Layout = ({ children, sidebar }: LayoutProps) => (
  <div className="layout">
    {sidebar && <aside>{sidebar}</aside>}
    <main>{children}</main>
  </div>
);
```

## refs

use explicit element type. prefer callback refs for cleanup.

```typescript
// good
const inputRef = useRef<HTMLInputElement>(null);

useEffect(() => {
  inputRef.current?.focus();
}, []);

// callback pattern
const measuredRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  if (!measuredRef.current) return;
  const observer = new ResizeObserver(...);
  observer.observe(measuredRef.current);
  return () => observer.disconnect();
}, []);
```

## context

types with provider component. consume with hook.

```typescript
interface ThemeContextValue {
  theme: "light" | "dark";
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const toggle = () => setTheme(t => t === "light" ? "dark" : "light");

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
};
```

## you might not need an effect

effects are for synchronizing with external systems (browser apis, non-react widgets, subscriptions). most ui logic belongs elsewhere.

### don't use effects for:

**transforming data for rendering**
```typescript
// bad
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// good — calculate during render
const fullName = `${firstName} ${lastName}`;
```

**caching expensive calculations**
```typescript
// bad
const [filtered, setFiltered] = useState([]);
useEffect(() => {
  setFiltered(items.filter(i => i.matches(query)));
}, [items, query]);

// good — useMemo for expensive work
const filtered = useMemo(() =>
  items.filter(i => i.matches(query)),
  [items, query]
);
```

**handling user events**
```typescript
// bad — event logic in effect
useEffect(() => {
  if (isInCart) showNotification("added!");
}, [isInCart]);

// good — event handler
const handleAdd = () => {
  addToCart(product);
  showNotification("added!");
};
```

**resetting state on prop changes**
```typescript
// bad
useEffect(() => {
  setComment("");
}, [userId]);

// good — use key
<profile key={userId} userId={userId} />
```

**notifying parent about state changes**
```typescript
// bad
useEffect(() => {
  onChange(isOn);
}, [isOn, onChange]);

// good — update together
const toggle = () => {
  const next = !isOn;
  setIsOn(next);
  onChange(next);
};
```

### do use effects for:

- subscriptions (websockets, browser events)
- manual dom manipulation
- analytics / logging on mount
- syncing with non-react widgets

## general

- no `use client` or `use server` directives
- prefer composition over props drilling
- keep components focused — data fetching near usage
- extract hooks when logic exceeds ~10 lines
