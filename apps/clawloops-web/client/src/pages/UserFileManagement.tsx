import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { FolderOpen, Trash2, Download, ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface User {
  username: string;
  fileCount: number;
  totalSize: number;
}

interface File {
  id: string;
  username: string;
  path: string;
  name: string;
  size: number;
  modifiedAt: number;
  isDirectory: boolean;
}

export default function UserFileManagement() {
  const [location, navigate] = useLocation();
  const [users, setUsers] = useState<User[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  // 解析路由参数
  useEffect(() => {
    const pathParts = location.split('/');
    if (pathParts.length === 4 && pathParts[2] === 'user-files') {
      const username = pathParts[3];
      setSelectedUser(username);
      loadUserFiles(username);
    } else {
      setSelectedUser(null);
      loadUsers();
    }
  }, [location]);

  // 加载所有用户
  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/admin/user-files/users', {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to load users');
      const data = await res.json();
      setUsers(data.users || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载用户失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载用户文件
  const loadUserFiles = async (username: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/admin/user-files/${username}/list`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to load files');
      const data = await res.json();
      setFiles(data.files || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载文件失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理用户点击
  const handleUserClick = (username: string) => {
    navigate(`/admin/user-files/${username}`);
  };

  // 处理返回
  const handleBack = () => {
    navigate('/admin/user-files');
  };

  // 处理删除文件
  const handleDelete = async (file: File) => {
    if (!selectedUser) return;
    
    if (!window.confirm(`确定要删除文件 ${file.name} 吗？`)) return;
    
    try {
      const res = await fetch(`/api/v1/admin/user-files/${selectedUser}/delete?path=${encodeURIComponent(file.path)}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to delete file');
      // 刷新文件列表
      loadUserFiles(selectedUser);
    } catch (e) {
      setError(e instanceof Error ? e.message : '删除文件失败');
    }
  };

  // 格式化文件大小
  const formatSize = (size: number) => {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`;
    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  };

  // 格式化时间
  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">用户文件管理</h1>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>错误</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-10">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : selectedUser ? (
        // 用户文件列表
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={handleBack}>
                  <ChevronLeft className="h-4 w-4" />
                  返回
                </Button>
                <CardTitle>{selectedUser} 的文件</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>文件名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>大小</TableHead>
                  <TableHead>修改时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center">
                      该用户没有文件
                    </TableCell>
                  </TableRow>
                ) : (
                  files.map((file) => (
                    <TableRow key={file.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {file.isDirectory ? (
                            <FolderOpen className="h-4 w-4 text-blue-500" />
                          ) : (
                            <div className="h-4 w-4 bg-gray-200 rounded" />
                          )}
                          <span>{file.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={file.isDirectory ? 'secondary' : 'default'}>
                          {file.isDirectory ? '目录' : '文件'}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatSize(file.size)}</TableCell>
                      <TableCell>{formatTime(file.modifiedAt)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() => handleDelete(file)}
                          >
                            <Trash2 className="h-4 w-4" />
                            删除
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        // 用户列表
        <Card>
          <CardHeader>
            <CardTitle>所有用户</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>用户名</TableHead>
                  <TableHead>文件数量</TableHead>
                  <TableHead>总大小</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center">
                      没有用户
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.username}>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>{user.fileCount}</TableCell>
                      <TableCell>{formatSize(user.totalSize)}</TableCell>
                      <TableCell>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleUserClick(user.username)}
                        >
                          查看文件
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
