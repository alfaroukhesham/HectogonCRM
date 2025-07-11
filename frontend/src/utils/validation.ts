export const validateEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

export const validatePassword = (password: string): boolean => {
  return password.length >= 12;
};

export const validatePasswordStrength = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 12) {
    errors.push('Password must be at least 12 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one digit');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateConfirmPassword = (password: string, confirmPassword: string): boolean => {
  return password === confirmPassword;
};

export const calculatePasswordStrength = (password: string): number => {
  let strength = 0;
  if (password.length >= 12) strength += 1;
  if (/[a-z]/.test(password)) strength += 1;
  if (/[A-Z]/.test(password)) strength += 1;
  if (/\d/.test(password)) strength += 1;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 1;
  return strength;
};

export const getPasswordStrengthColor = (passwordStrength: number): string => {
  switch (passwordStrength) {
    case 0:
    case 1:
      return 'bg-red-500';
    case 2:
      return 'bg-yellow-500';
    case 3:
      return 'bg-blue-500';
    case 4:
    case 5:
      return 'bg-green-500';
    default:
      return 'bg-gray-300';
  }
};

export const getPasswordStrengthText = (passwordStrength: number): string => {
  switch (passwordStrength) {
    case 0:
    case 1:
      return 'Weak';
    case 2:
      return 'Fair';
    case 3:
      return 'Good';
    case 4:
    case 5:
      return 'Strong';
    default:
      return '';
  }
}; 
 
 