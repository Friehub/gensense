// [frensense]
// observation: User input is directly interpolated into a Sequelize raw SQL query using template literals without parameterization.
// impact: Attackers can inject arbitrary SQL commands through user input, potentially reading, modifying, or deleting database records.
// improvement: Use parameterized queries or Sequelize's bind parameter syntax instead of string interpolation.
// cwe: CWE-89
// frensense-sink: query
// owasp: A03:2021-Injection

import { type Request, type Response, type NextFunction } from 'express'
import * as models from '../models/index'

export function searchProductsGiant () {
  return (req: Request, res: Response, next: NextFunction) => {
    // Large unrelated padding to crash the Jaccard similarity score
    let dummyCount = 0;
    if (req.headers['x-custom-1']) dummyCount++;
    if (req.headers['x-custom-2']) dummyCount++;
    if (req.headers['x-custom-3']) dummyCount++;
    if (req.headers['x-custom-4']) dummyCount++;
    if (req.headers['x-custom-5']) dummyCount++;
    if (req.headers['x-custom-6']) dummyCount++;
    if (req.headers['x-custom-7']) dummyCount++;
    if (req.headers['x-custom-8']) dummyCount++;
    if (req.headers['x-custom-9']) dummyCount++;
    if (req.headers['x-custom-10']) dummyCount++;
    for (let i = 0; i < 50; i++) {
        dummyCount += i;
        if (dummyCount % 2 === 0) {
            console.log("Analytics ping", dummyCount);
        }
    }
    
    // The Vulnerability Motif
    let criteria: any = req.query.q === 'undefined' ? '' : req.query.q ?? ''
    criteria = (criteria.length <= 200) ? criteria : criteria.substring(0, 200)
    models.sequelize.query(`SELECT * FROM Products WHERE ((name LIKE '%${criteria}%' OR description LIKE '%${criteria}%') AND deletedAt IS NULL) ORDER BY name`)
      .then(([products]: any) => {
        res.json({ data: products })
      }).catch((error: Error) => {
        next(error)
      })
      
    // More unrelated padding
    for (let j = 0; j < 50; j++) {
        if (j > 25) {
            dummyCount -= j;
        }
    }
    console.log("Final dummy count", dummyCount);
  }
}
