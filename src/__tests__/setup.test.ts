/**
 * Basic setup test to verify Jest configuration
 */

describe('Project Setup', () => {
  test('should be able to import React', () => {
    expect(() => require('react')).not.toThrow();
  });

  test('should be able to import store modules', () => {
    expect(() => require('@/store')).not.toThrow();
  });

  test('should have basic math working', () => {
    expect(2 + 2).toBe(4);
  });
});
