import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { type CurrentUser, getMe, login as apiLogin, register as apiRegister } from "../api/client";

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
    fleetName: string
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("tiq_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      localStorage.removeItem("tiq_token");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    localStorage.setItem("tiq_token", access_token);
    const me = await getMe();
    setUser(me);
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string, fleetName: string) => {
      const { access_token } = await apiRegister(email, password, fullName, fleetName);
      localStorage.setItem("tiq_token", access_token);
      const me = await getMe();
      setUser(me);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("tiq_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
