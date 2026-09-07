// SAFE: Uses Sequelize parameterized query with bind parameters but embedded in a giant function
import { type Request, type Response, type NextFunction } from 'express'
import * as models from '../models/index'

export function searchProductsGiantSafe () {
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
    
    // The Safe Motif
    let criteria: any = req.query.q === 'undefined' ? '' : req.query.q ?? ''
    criteria = (criteria.length <= 200) ? criteria : criteria.substring(0, 200)
    models.sequelize.query(
      `SELECT * FROM Products WHERE ((name LIKE :criteria OR description LIKE :criteria) AND deletedAt IS NULL) ORDER BY name`,
      { replacements: { criteria: `%${criteria}%` } }
    )
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
