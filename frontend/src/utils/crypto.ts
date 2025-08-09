import CryptoJS from 'crypto-js';

/**
 * 密码加密工具类
 */
export class PasswordCrypto {
  /**
   * 对密码进行SHA256哈希
   * @param password 原始密码
   * @returns 哈希后的密码
   */
  static hashPassword(password: string): string {
    return CryptoJS.SHA256(password).toString();
  }

  /**
   * 使用动态盐值哈希密码
   * @param password 原始密码
   * @param salt 盐值（可以是用户名或服务器提供的随机值）
   * @returns 哈希后的密码
   */
  static hashPasswordWithSalt(password: string, salt: string): string {
    return CryptoJS.SHA256(password + salt).toString();
  }

  /**
   * 生成带时间戳的密码哈希（防重放攻击）
   * @param password 原始密码
   * @param username 用户名
   * @returns 包含哈希值和时间戳的对象
   */
  static hashPasswordWithTimestamp(password: string, username: string): {
    hash: string;
    timestamp: number;
    nonce: string;
  } {
    const timestamp = Date.now();
    const nonce = Math.random().toString(36).substring(7);
    
    // 组合多个因素生成哈希
    const combinedString = `${username}:${password}:${timestamp}:${nonce}`;
    const hash = CryptoJS.SHA256(combinedString).toString();
    
    return {
      hash,
      timestamp,
      nonce
    };
  }

  /**
   * 验证时间戳是否在有效期内（默认5分钟）
   * @param timestamp 时间戳
   * @param maxAge 最大有效期（毫秒）
   * @returns 是否有效
   */
  static isTimestampValid(timestamp: number, maxAge: number = 5 * 60 * 1000): boolean {
    const now = Date.now();
    return (now - timestamp) <= maxAge;
  }
}

// 导出便捷方法
export const hashPassword = PasswordCrypto.hashPassword;
export const hashPasswordWithSalt = PasswordCrypto.hashPasswordWithSalt;
export const hashPasswordWithTimestamp = PasswordCrypto.hashPasswordWithTimestamp;